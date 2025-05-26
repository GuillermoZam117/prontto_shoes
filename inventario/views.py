from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Inventario, Traspaso, TraspasoItem
from .serializers import InventarioSerializer, TraspasoSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.db.models import F # Import F object for atomic updates
from tiendas.models import Tienda
from productos.models import Producto
from django.contrib.auth.decorators import login_required
from django.db.models import Q

# Create your views here.

class InventarioViewSet(viewsets.ModelViewSet):
    queryset = Inventario.objects.all()
    serializer_class = InventarioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tienda', 'producto', 'cantidad_actual', 'fecha_registro']

class TraspasoViewSet(viewsets.ModelViewSet):
    queryset = Traspaso.objects.all()
    serializer_class = TraspasoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tienda_origen', 'tienda_destino', 'estado', 'fecha']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def confirmar_traspaso(self, request, pk=None):
        """
        Confirms a transfer, updating the inventory in origin and destination stores for each item.
        """
        traspaso = self.get_object()

        if traspaso.estado != 'pendiente':
            return Response({"error": f"El traspaso ya ha sido {traspaso.estado}."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            for item in traspaso.items.all():
                # Decrease inventory in origin store
                origin_inventory = Inventario.objects.select_for_update().get(
                    tienda=traspaso.tienda_origen,
                    producto=item.producto
                )
                if origin_inventory.cantidad_actual < item.cantidad:
                    raise ValidationError(f"Cantidad insuficiente para el producto {item.producto.codigo} en la tienda de origen.")
                origin_inventory.cantidad_actual = F('cantidad_actual') - item.cantidad
                origin_inventory.save()

                # Increase inventory in destination store
                destination_inventory, created = Inventario.objects.select_for_update().get_or_create(
                    tienda=traspaso.tienda_destino,
                    producto=item.producto,
                    defaults={'cantidad_actual': 0}
                )
                destination_inventory.cantidad_actual = F('cantidad_actual') + item.cantidad
                destination_inventory.save()

            # Update transfer status
            traspaso.estado = 'completado'
            traspaso.save()

        serializer = self.get_serializer(traspaso)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancelar_traspaso(self, request, pk=None):
        """
        Cancels a pending transfer.
        """
        traspaso = self.get_object()

        if traspaso.estado != 'pendiente':
            return Response({"error": f"El traspaso ya ha sido {traspaso.estado}. Solo se pueden cancelar traspasos pendientes."}, status=status.HTTP_400_BAD_REQUEST)

        traspaso.estado = 'cancelado'
        traspaso.save()

        serializer = self.get_serializer(traspaso)
        return Response(serializer.data)

class InventarioActualReporteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InventarioSerializer  # Add this for DRF Spectacular
    """
    Devuelve un reporte del inventario actual agrupado por tienda y producto.
    """
    def get(self, request):
        data = []
        inventarios = Inventario.objects.select_related('tienda', 'producto').all()
        for inv in inventarios:
            data.append({
                'tienda_id': inv.tienda.id,
                'tienda_nombre': inv.tienda.nombre,
                'producto_id': inv.producto.id,
                'producto_codigo': inv.producto.codigo,
                'producto_nombre': str(inv.producto),
                'cantidad_actual': inv.cantidad_actual,
                'fecha_registro': inv.fecha_registro
            })
        return Response(data)

# Frontend views for the inventory app
@login_required
def inventario_list(request):
    """
    Display inventory levels across stores with HTMX support.
    Allows filtering by product, store, or low stock status.
    """
    # Get filter parameters
    search_query = request.GET.get('q', '')
    tienda_id = request.GET.get('tienda', '')
    stock_bajo = request.GET.get('stock_bajo', False)
    
    # Base query
    inventario = Inventario.objects.select_related('tienda', 'producto')
      # Apply filters
    if search_query:
        inventario = inventario.filter(
            Q(producto__codigo__icontains=search_query) | 
            Q(producto__marca__icontains=search_query) |
            Q(producto__modelo__icontains=search_query) |
            Q(producto__color__icontains=search_query) |
            Q(tienda__nombre__icontains=search_query)
        )
    
    if tienda_id:
        inventario = inventario.filter(tienda_id=tienda_id)
    
    if stock_bajo:
        # Filter products with stock below minimum level
        inventario = inventario.filter(cantidad_actual__lt=F('producto__stock_minimo'))
      # Order results
    inventario = inventario.order_by('producto__marca', 'producto__modelo', 'tienda__nombre')
      # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        # Calculate metrics for the filtered results
        sin_stock = inventario.filter(cantidad_actual__lte=0).count()
        stock_bajo_count = inventario.filter(
            cantidad_actual__gt=0,
            cantidad_actual__lt=F('producto__stock_minimo')
        ).count()
        stock_normal_count = inventario.filter(
            cantidad_actual__gte=F('producto__stock_minimo')
        ).count()
        
        # Return only the table partial for HTMX requests
        context = {
            'inventario': inventario,
            'search_query': search_query,
            'tienda_seleccionada': tienda_id,
            'stock_bajo': stock_bajo,
            'sin_stock': sin_stock,
            'stock_bajo_count': stock_bajo_count,
            'stock_normal_count': stock_normal_count,
        }
        return render(request, 'inventario/partials/inventario_table.html', context)
      # Full page render for regular requests
    # Calculate inventory metrics for all items
    all_inventory = Inventario.objects.all()
    sin_stock = all_inventory.filter(cantidad_actual__lte=0).count()
    stock_bajo_count = all_inventory.filter(
        cantidad_actual__gt=0,
        cantidad_actual__lt=F('producto__stock_minimo')
    ).count()
    stock_normal_count = all_inventory.filter(
        cantidad_actual__gte=F('producto__stock_minimo')
    ).count()
    
    # Get stores for filter dropdown
    tiendas = Tienda.objects.all()
    
    context = {
        'inventario': inventario,
        'tiendas': tiendas,
        'search_query': search_query,
        'tienda_seleccionada': tienda_id,
        'stock_bajo': stock_bajo,
        'sin_stock': sin_stock,
        'stock_bajo_count': stock_bajo_count,
        'stock_normal_count': stock_normal_count,
    }
    
    return render(request, 'inventario/inventario_list.html', context)

@login_required
def traspaso_list(request):
    """
    Display a list of inventory transfers between stores
    """
    # Get filter parameters
    estado = request.GET.get('estado', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    
    # Base query
    traspasos = Traspaso.objects.select_related('tienda_origen', 'tienda_destino', 'created_by').order_by('-fecha')
    
    # Apply filters
    if estado:
        traspasos = traspasos.filter(estado=estado)
    
    if fecha_desde:
        traspasos = traspasos.filter(fecha__gte=fecha_desde)
    
    if fecha_hasta:
        traspasos = traspasos.filter(fecha__lte=fecha_hasta)
    
    context = {
        'traspasos': traspasos,
        'estado': estado,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    
    return render(request, 'inventario/traspaso_list.html', context)

@login_required
def traspaso_detail(request, pk):
    """
    Display details of a specific transfer
    """
    traspaso = get_object_or_404(Traspaso.objects.select_related('tienda_origen', 'tienda_destino', 'created_by'), pk=pk)
    items = traspaso.items.select_related('producto').all()
    
    context = {
        'traspaso': traspaso,
        'items': items,
    }
    
    return render(request, 'inventario/traspaso_detail.html', context)

@login_required
def traspaso_create(request):
    """
    Create a new inventory transfer between stores
    """
    tiendas = Tienda.objects.all()
    
    if request.method == 'POST':
        # This is a placeholder for form processing - to be implemented later
        # Will need to handle traspaso and its related items creation
        return redirect('inventario:traspasos')
    
    context = {
        'tiendas': tiendas,
    }
    
    return render(request, 'inventario/traspaso_form.html', context)
