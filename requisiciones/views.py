from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Requisicion, DetalleRequisicion
from .serializers import RequisicionSerializer, DetalleRequisicionSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from django.utils.dateparse import parse_date
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Count, Sum
from productos.models import Producto
from clientes.models import Cliente

# Create your views here.

@extend_schema(tags=["Requisiciones"])
class RequisicionViewSet(viewsets.ModelViewSet):
    queryset = Requisicion.objects.all()
    serializer_class = RequisicionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cliente', 'fecha', 'estado']

    def get_queryset(self):
        # Allow admin/staff to see all requisitions
        if self.request.user and self.request.user.is_staff:
            return Requisicion.objects.all()
        # Allow only the client associated with the user to see their requisitions
        # This assumes a link between User and Cliente, e.g., request.user.cliente
        if self.request.user and hasattr(self.request.user, 'cliente'):
            return Requisicion.objects.filter(cliente=self.request.user.cliente)
        return Requisicion.objects.none() # No requisitions for unauthenticated or unlinked users

    def perform_create(self, serializer):
        # Associate the requisition with the client of the authenticated user
        # This assumes a link between User and Cliente
        if self.request.user and hasattr(self.request.user, 'cliente'):
            serializer.save(cliente=self.request.user.cliente)
        else:
            # Handle case where user is not linked to a client (should be prevented by permissions/validation)
            raise ValidationError("User is not associated with a client.")

    @action(detail=False, methods=['get'], url_path='my-requisitions')
    def my_requisitions(self, request):
        """
        Get requisitions for the authenticated client.
        """
        queryset = self.get_queryset() # Use the filtered queryset
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

@extend_schema(tags=["Requisiciones"])
class DetalleRequisicionViewSet(viewsets.ModelViewSet):
    queryset = DetalleRequisicion.objects.all()
    serializer_class = DetalleRequisicionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['requisicion', 'producto', 'cantidad']

@extend_schema(tags=["Reportes"])
class RequisicionesReporteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RequisicionSerializer  # Add this for DRF Spectacular
    """
    Devuelve un reporte de requisiciones realizadas, mostrando cliente, productos, cantidades, estado y fecha.
    """
    def get(self, request):
        from .models import Requisicion
        data = []
        requisiciones = Requisicion.objects.select_related('cliente').prefetch_related('detalles__producto').all()
        for req in requisiciones:
            detalles = []
            for det in req.detalles.all():
                detalles.append({
                    'producto_id': det.producto.id,
                    'producto_codigo': det.producto.codigo,
                    'producto_nombre': str(det.producto),
                    'cantidad': det.cantidad
                })
            data.append({
                'requisicion_id': req.id,
                'cliente_id': req.cliente.id,
                'cliente_nombre': req.cliente.nombre,
                'fecha': req.fecha,
                'estado': req.estado,
                'detalles': detalles
            })
        return Response(data)

# Frontend views
def requisicion_list(request):
    """Vista para listar requisiciones"""
    # Get filter parameters
    cliente_id = request.GET.get('cliente', '')
    estado = request.GET.get('estado', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    
    # Base query with related models
    requisiciones = Requisicion.objects.select_related('cliente', 'created_by').prefetch_related('detalles').all()
    
    # Apply filters
    if cliente_id:
        requisiciones = requisiciones.filter(cliente_id=cliente_id)
    
    if estado:
        requisiciones = requisiciones.filter(estado=estado)
    
    if fecha_desde:
        requisiciones = requisiciones.filter(fecha__date__gte=parse_date(fecha_desde))
    
    if fecha_hasta:
        requisiciones = requisiciones.filter(fecha__date__lte=parse_date(fecha_hasta))
    
    # Get related data for filters
    clientes = Cliente.objects.all()
    
    # Calculate statistics for summary cards
    total_pendientes = requisiciones.filter(estado='pendiente').count()
    total_procesadas = requisiciones.filter(estado='procesada').count()
    total_canceladas = requisiciones.filter(estado='cancelada').count()
    
    context = {
        'requisiciones': requisiciones,
        'clientes': clientes,
        'cliente_seleccionado': cliente_id,
        'estado_seleccionado': estado,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'total_pendientes': total_pendientes,
        'total_procesadas': total_procesadas,
        'total_canceladas': total_canceladas
    }
    
    return render(request, 'requisiciones/requisicion_list.html', context)

def requisicion_detail(request, pk):
    """Vista de detalle de una requisición"""
    requisicion = get_object_or_404(Requisicion, pk=pk)
    
    context = {
        'requisicion': requisicion,
    }
    
    return render(request, 'requisiciones/requisicion_detail.html', context)

def requisicion_create(request):
    """Vista para crear una nueva requisición"""
    clientes = Cliente.objects.all()
    productos = Producto.objects.all().select_related('proveedor')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get form data
                cliente_id = request.POST.get('cliente')
                
                # Validate required fields
                if not cliente_id:
                    messages.error(request, "El cliente es obligatorio.")
                    return redirect('requisiciones:nueva')
                
                # Get client
                cliente = get_object_or_404(Cliente, pk=cliente_id)
                
                # Create requisicion
                requisicion = Requisicion.objects.create(
                    cliente=cliente,
                    estado='pendiente',
                    created_by=request.user
                )
                
                # Process product items
                producto_ids = request.POST.getlist('producto[]')
                cantidades = request.POST.getlist('cantidad[]')
                
                if len(producto_ids) != len(cantidades):
                    messages.error(request, "Error en los datos de productos.")
                    requisicion.delete()
                    return redirect('requisiciones:nueva')
                
                for i in range(len(producto_ids)):
                    producto_id = producto_ids[i]
                    cantidad = cantidades[i]
                    
                    if not producto_id or not cantidad or int(cantidad) <= 0:
                        continue
                    
                    producto = get_object_or_404(Producto, pk=producto_id)
                    
                    DetalleRequisicion.objects.create(
                        requisicion=requisicion,
                        producto=producto,
                        cantidad=cantidad
                    )
                
                if requisicion.detalles.count() == 0:
                    messages.error(request, "Debe agregar al menos un producto.")
                    requisicion.delete()
                    return redirect('requisiciones:nueva')
                
                messages.success(request, f"Requisición {requisicion.id} creada correctamente.")
                return redirect('requisiciones:detalle', pk=requisicion.id)
                
        except Exception as e:
            messages.error(request, f"Error al crear la requisición: {str(e)}")
    
    context = {
        'clientes': clientes,
        'productos': productos,
    }
    
    return render(request, 'requisiciones/requisicion_form.html', context)

def requisicion_edit(request, pk):
    """Vista para editar una requisición"""
    requisicion = get_object_or_404(Requisicion, pk=pk)
    
    # Only allow editing for pending requisitions
    if requisicion.estado != 'pendiente':
        messages.error(request, "Solo se pueden editar requisiciones en estado 'pendiente'.")
        return redirect('requisiciones:detalle', pk=pk)
    
    clientes = Cliente.objects.all()
    productos = Producto.objects.all().select_related('proveedor')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Process product items
                producto_ids = request.POST.getlist('producto[]')
                cantidades = request.POST.getlist('cantidad[]')
                
                if len(producto_ids) != len(cantidades):
                    messages.error(request, "Error en los datos de productos.")
                    return redirect('requisiciones:editar', pk=pk)
                
                # Remove existing details
                requisicion.detalles.all().delete()
                
                # Add new details
                for i in range(len(producto_ids)):
                    producto_id = producto_ids[i]
                    cantidad = cantidades[i]
                    
                    if not producto_id or not cantidad or int(cantidad) <= 0:
                        continue
                    
                    producto = get_object_or_404(Producto, pk=producto_id)
                    
                    DetalleRequisicion.objects.create(
                        requisicion=requisicion,
                        producto=producto,
                        cantidad=cantidad
                    )
                
                if requisicion.detalles.count() == 0:
                    messages.error(request, "Debe agregar al menos un producto.")
                    return redirect('requisiciones:editar', pk=pk)
                
                messages.success(request, f"Requisición {requisicion.id} actualizada correctamente.")
                return redirect('requisiciones:detalle', pk=pk)
                
        except Exception as e:
            messages.error(request, f"Error al actualizar la requisición: {str(e)}")
    
    context = {
        'requisicion': requisicion,
        'clientes': clientes,
        'productos': productos,
    }
    
    return render(request, 'requisiciones/requisicion_form.html', context)

def requisicion_report(request):
    """Vista para generar reportes de requisiciones"""
    # Get filter parameters
    cliente_id = request.GET.get('cliente', '')
    estado = request.GET.get('estado', '')
    fecha_desde = request.GET.get('fecha_desde', (timezone.now().replace(day=1)).strftime('%Y-%m-%d'))
    fecha_hasta = request.GET.get('fecha_hasta', timezone.now().strftime('%Y-%m-%d'))
    
    # Base query with related models
    requisiciones = Requisicion.objects.select_related('cliente', 'created_by').prefetch_related('detalles__producto').all()
    
    # Apply filters
    if cliente_id:
        requisiciones = requisiciones.filter(cliente_id=cliente_id)
    
    if estado:
        requisiciones = requisiciones.filter(estado=estado)
    
    if fecha_desde:
        requisiciones = requisiciones.filter(fecha__date__gte=parse_date(fecha_desde))
    
    if fecha_hasta:
        requisiciones = requisiciones.filter(fecha__date__lte=parse_date(fecha_hasta))
    
    # Get related data for filters
    clientes = Cliente.objects.all()
    
    # Group data for charts
    requisiciones_por_estado = requisiciones.values('estado').annotate(count=Count('id'))
    
    # Calculate summary metrics
    total_requisiciones = requisiciones.count()
    productos_solicitados = DetalleRequisicion.objects.filter(requisicion__in=requisiciones).count()
    
    context = {
        'requisiciones': requisiciones,
        'clientes': clientes,
        'cliente_seleccionado': cliente_id,
        'estado_seleccionado': estado,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'requisiciones_por_estado': requisiciones_por_estado,
        'total_requisiciones': total_requisiciones,
        'productos_solicitados': productos_solicitados
    }
    
    return render(request, 'requisiciones/requisicion_report.html', context)
