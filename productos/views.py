from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Producto, Proveedor, Tienda, Catalogo
from .serializers import ProductoSerializer, CatalogoSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from inventario.models import Inventario # Import Inventario model
from django.db.models import F, Sum, OuterRef, Subquery
from django.db import models
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import filters
from rest_framework.parsers import MultiPartParser, FormParser
from .forms import ProductoForm, ProductoImportForm
from django.db.models import Q
import tempfile
import os

@extend_schema(tags=["Productos"])
class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['codigo', 'marca', 'modelo', 'color', 'proveedor', 'tienda', 'temporada', 'oferta', 'catalogo']
    search_fields = ['codigo', 'nombre', 'marca', 'modelo']

    @extend_schema(
        description="Importar catálogo de productos desde un archivo Excel.",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {'type': 'string', 'format': 'binary'}
                }
            }
        },
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def import_excel(self, request):
        if 'file' not in request.data:
            return Response({"error": "No se proporcionó ningún archivo"}, status=status.HTTP_400_BAD_REQUEST)
        
        file_obj = request.data['file']
        
        # Save the file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in file_obj.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        try:
            # Only import pandas and openpyxl when needed to avoid overhead
            import pandas as pd
            
            # Process Excel file
            df = pd.read_excel(temp_file_path)
            
            # Here we would process and save data from the Excel file
            # This is a placeholder - actual implementation will depend on the Excel structure
            
            return Response({"message": "Importación exitosa"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        finally:
            os.unlink(temp_file_path)

    @extend_schema(
        description="Listar productos del catálogo vigente con disponibilidad de inventario.",
        responses={200: ProductoSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='active-catalog')
    def active_catalog(self, request):
        """
        Get products from the currently active catalog including inventory availability.
        This endpoint is intended for distributors to view available products for requisitions.
        """
        # Find the active catalog(s)
        active_catalogs = Catalogo.objects.filter(activo=True)

        if not active_catalogs.exists():
            return Response({"message": "No hay catálogos activos en este momento."}, status=status.HTTP_404_NOT_FOUND)

        # Get products from active catalogs and annotate with inventory quantity
        # Using Subquery to get inventory quantity efficiently
        inventory_subquery = None
        # Attempt to get the client's store if the user has a client profile
        if hasattr(self.request.user, 'cliente_profile') and self.request.user.cliente_profile and self.request.user.cliente_profile.tienda:
            tienda_cliente = self.request.user.cliente_profile.tienda
            inventory_subquery = Inventario.objects.filter(
                producto=OuterRef('pk'),
                tienda=tienda_cliente
            ).values('cantidad_actual')[:1]
        else:
            # Fallback: if no specific store, sum inventory from all stores or handle as per business logic
            # For now, let's sum all inventory for the product across all stores.
            # This might need adjustment based on precise requirements for users without a specific client store.
            inventory_subquery = Inventario.objects.filter(
                producto=OuterRef('pk')
            ).values('producto').annotate(total_stock=Sum('cantidad_actual')).values('total_stock')


        if inventory_subquery:
            queryset = Producto.objects.filter(catalogo__in=active_catalogs).annotate(
                cantidad_disponible=Subquery(inventory_subquery, output_field=models.IntegerField())
            )
        else: # Should not happen if logic above is correct, but as a safeguard
            queryset = Producto.objects.filter(catalogo__in=active_catalogs)


        # Handle pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)



# Add Catalogo ViewSet
@extend_schema(tags=["Catalogos"])
class CatalogoViewSet(viewsets.ModelViewSet):
    queryset = Catalogo.objects.all()
    serializer_class = CatalogoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['nombre', 'temporada', 'es_oferta', 'activo', 'fecha_inicio_vigencia', 'fecha_fin_vigencia']

    @extend_schema(
        description="Activa un catálogo y desactiva otros (opcionalmente por tipo).",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'catalogo_id': {'type': 'integer', 'description': 'ID del catálogo a activar'},
                    'desactivar_otros_temporada': {'type': 'boolean', 'description': 'Desactivar otros catálogos de la misma temporada', 'default': False},
                    'desactivar_otros_oferta': {'type': 'boolean', 'description': 'Desactivar otros catálogos de oferta', 'default': False},
                    'desactivar_todos_anteriores': {'type': 'boolean', 'description': 'Desactivar todos los catálogos anteriores de cualquier tipo', 'default': False}
                },
                'required': ['catalogo_id']
            }
        },
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['post'])
    def activar_catalogo(self, request):
        catalogo_id = request.data.get('catalogo_id')
        desactivar_otros_temporada = request.data.get('desactivar_otros_temporada', False)
        desactivar_otros_oferta = request.data.get('desactivar_otros_oferta', False)
        desactivar_todos_anteriores = request.data.get('desactivar_todos_anteriores', False)

        if not catalogo_id:
             return Response({"error": "Debe proporcionar el ID del catálogo a activar."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            catalogo_a_activar = Catalogo.objects.get(id=catalogo_id)
        except Catalogo.DoesNotExist:
            return Response({"error": "Catálogo no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            # Deactivate other catalogs based on parameters
            if desactivar_todos_anteriores:
                Catalogo.objects.exclude(id=catalogo_id).update(activo=False)
            else:
                if desactivar_otros_temporada and catalogo_a_activar.temporada:
                     Catalogo.objects.filter(temporada=catalogo_a_activar.temporada).exclude(id=catalogo_id).update(activo=False)
                if desactivar_otros_oferta and catalogo_a_activar.es_oferta:
                     Catalogo.objects.filter(es_oferta=True).exclude(id=catalogo_id).update(activo=False)

            # Activate the target catalog
            catalogo_a_activar.activo = True
            catalogo_a_activar.save()

        return Response({"message": f"Catálogo '{catalogo_a_activar.nombre}' activado exitosamente."}, status=status.HTTP_200_OK)


# Frontend Views
@login_required
def producto_list(request):
    search_query = request.GET.get('q', '')
    
    if search_query:
        productos = Producto.objects.filter(
            Q(codigo__icontains=search_query) | 
            Q(nombre__icontains=search_query) | 
            Q(marca__icontains=search_query) | 
            Q(modelo__icontains=search_query)
        )
    else:
        productos = Producto.objects.all()
    
    context = {
        'productos': productos,
        'search_query': search_query,
    }
    return render(request, 'productos/producto_list.html', context)

@login_required
def producto_detail(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    context = {
        'producto': producto,
    }
    return render(request, 'productos/producto_detail.html', context)

@login_required
def producto_create(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.created_by = request.user
            producto.save()
            messages.success(request, f"Producto '{producto.codigo} - {producto.marca} {producto.modelo}' creado exitosamente.")
            return redirect('productos:lista')
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = ProductoForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Nuevo Producto'
    }
    return render(request, 'productos/producto_form.html', context)

@login_required
def producto_edit(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            producto_actualizado = form.save(commit=False)
            producto_actualizado.updated_by = request.user
            producto_actualizado.save()
            form.save_m2m() # Para guardar relaciones ManyToMany si las hubiera en el futuro
            messages.success(request, f"Producto '{producto_actualizado.codigo} - {producto_actualizado.marca} {producto_actualizado.modelo}' actualizado exitosamente.")
            return redirect('productos:detalle', pk=producto_actualizado.pk)
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = ProductoForm(instance=producto)
    
    context = {
        'form': form,
        'producto': producto, # Para mostrar info adicional si es necesario en la plantilla
        'titulo': f'Editar Producto: {producto.codigo}'
    }
    return render(request, 'productos/producto_form.html', context)

@login_required
def producto_import(request):
    # La plantilla producto_import.html maneja la subida del formulario vía AJAX
    # directamente al endpoint de la API /api/productos/import_excel/.
    # Esta vista de Django solo necesita renderizar la plantilla.
    context = {
        'titulo': 'Importar Productos desde Excel'
    }
    return render(request, 'productos/producto_import.html', context)

# Create your views here.
