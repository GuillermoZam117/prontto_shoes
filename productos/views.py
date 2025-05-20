from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Producto, Proveedor, Tienda, Catalogo
from .serializers import ProductoSerializer, CatalogoSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiExample
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from inventario.models import Inventario # Import Inventario model
from django.db.models import F, Sum, OuterRef, Subquery
from django.db import models

@extend_schema(tags=["Productos"])
class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['codigo', 'marca', 'modelo', 'color', 'proveedor', 'tienda', 'temporada', 'oferta', 'catalogo']

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
    @action(detail=False, methods=['post'])
    def import_catalogo(self, request):
        import pandas as pd # Moved import here
        import openpyxl # Moved import here

        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No se proporcionó ningún archivo."}, status=status.HTTP_400_BAD_REQUEST)

        if not file.name.endswith(('.xls', '.xlsx')):
            return Response({"error": "El archivo debe ser un archivo Excel (.xls o .xlsx)."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_excel(file)
        except Exception as e:
            return Response({"error": f"Error al leer el archivo Excel: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # Define the expected columns (adjust as per your Excel structure)
        expected_columns = ['codigo', 'marca', 'modelo', 'color', 'propiedad', 'costo', 'precio', 'numero_pagina', 'temporada', 'oferta', 'admite_devolucion', 'proveedor', 'tienda', 'catalogo']
        if not all(col in df.columns for col in expected_columns):
            missing_cols = [col for col in expected_columns if col not in df.columns]
            return Response({"error": f"Faltan columnas en el archivo Excel: {missing_cols}"}, status=status.HTTP_400_BAD_REQUEST)

        imported_count = 0
        errors = {}

        with transaction.atomic():
            for index, row in df.iterrows():
                codigo = row['codigo']
                try:
                    # Get or create related objects (Proveedor, Tienda, and Catalogo)
                    proveedor_nombre = row['proveedor']
                    tienda_nombre = row['tienda']
                    catalogo_nombre = row['catalogo']
                    
                    try:
                        proveedor = Proveedor.objects.get(nombre=proveedor_nombre)
                    except Proveedor.DoesNotExist:
                        errors[codigo] = f"Proveedor '{proveedor_nombre}' no encontrado."
                        continue
                        
                    try:
                        tienda = Tienda.objects.get(nombre=tienda_nombre)
                    except Tienda.DoesNotExist:
                        errors[codigo] = f"Tienda '{tienda_nombre}' no encontrada."
                        continue
                        
                    try:
                        catalogo = Catalogo.objects.get(nombre=catalogo_nombre)
                    except Catalogo.DoesNotExist:
                         errors[codigo] = f"Catálogo '{catalogo_nombre}' no encontrado. Cree el catálogo primero."
                         continue

                    # Create or update the product
                    producto, created = Producto.objects.update_or_create(
                        codigo=codigo,
                        defaults={
                            'marca': row['marca'],
                            'modelo': row['modelo'],
                            'color': row['color'],
                            'propiedad': row['propiedad'],
                            'costo': row['costo'],
                            'precio': row['precio'],
                            'numero_pagina': row['numero_pagina'],
                            'temporada': row['temporada'],
                            'oferta': row['oferta'],
                            'admite_devolucion': row['admite_devolucion'],
                            'proveedor': proveedor,
                            'tienda': tienda,
                            'catalogo': catalogo,
                        }
                    )
                    imported_count += 1
                except Exception as e:
                    errors[codigo] = f"Error al procesar producto {codigo}: {e}"
                    transaction.set_rollback(True)
                    return Response({"message": f"Error durante la importación. {imported_count} productos procesados antes del error.", "error_details": errors}, status=status.HTTP_400_BAD_REQUEST)

        if errors:
            return Response({"message": f"Se importaron {imported_count} productos con errores.", "errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": f"Catálogo importado exitosamente. {imported_count} productos procesados."}, status=status.HTTP_200_OK)

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
        inventory_subquery = Inventario.objects.filter(
            producto=OuterRef('pk'),
            tienda=self.request.user.cliente.tienda # Assuming user is linked to a client and client to a store
        ).values('cantidad_actual')[:1]

        queryset = Producto.objects.filter(catalogo__in=active_catalogs).annotate(
            cantidad_disponible=Subquery(inventory_subquery, output_field=models.IntegerField())
        )

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


# Create your views here.
