from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Caja, NotaCargo, Factura, TransaccionCaja
from .serializers import CajaSerializer, NotaCargoSerializer, FacturaSerializer, TransaccionCajaSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from django.db import transaction, IntegrityError
from django.db.models import Sum, Q
from datetime import date, datetime
from django.contrib.auth import get_user_model
from tiendas.models import Tienda
from django.contrib import messages
from ventas.models import Pedido

# Frontend views
def caja_list(request):
    """Vista para listar cajas del día o históricas"""
    # Get filter parameters
    fecha = request.GET.get('fecha', date.today().isoformat())
    tienda_id = request.GET.get('tienda', '')
    ver_historial = request.GET.get('historial', False)
    
    # Base query
    cajas = Caja.objects.select_related('tienda', 'created_by')
    
    # Apply filters
    if not ver_historial:
        cajas = cajas.filter(fecha=fecha)
    
    if tienda_id:
        cajas = cajas.filter(tienda_id=tienda_id)
    
    # Get tiendas for filter dropdown
    tiendas = Tienda.objects.all()
    
    # Calculate statistics
    cajas_abiertas_count = cajas.filter(cerrada=False).count()
    ingresos_dia = cajas.aggregate(total=Sum('ingresos'))['total'] or 0
    saldo_total = cajas.aggregate(total=Sum('saldo_final'))['total'] or 0
    
    context = {
        'cajas': cajas,
        'tiendas': tiendas,
        'fecha': fecha,
        'tienda_seleccionada': tienda_id,
        'ver_historial': ver_historial,
        'cajas_abiertas_count': cajas_abiertas_count,
        'ingresos_dia': ingresos_dia,
        'saldo_total': saldo_total,
    }
    
    return render(request, 'caja/caja_list.html', context)

def abrir_caja(request):
    """Vista para abrir una caja"""
    tiendas = Tienda.objects.all()
    today = date.today()
    
    if request.method == 'POST':
        tienda_id = request.POST.get('tienda')
        fondo_inicial = request.POST.get('fondo_inicial', 0)
        
        try:
            # Validate data
            if not tienda_id:
                messages.error(request, "Debe seleccionar una tienda.")
                return redirect('caja:abrir')
            
            # Check if already opened
            if Caja.objects.filter(tienda_id=tienda_id, fecha=today, cerrada=False).exists():
                messages.error(request, "Ya existe una caja abierta para esta tienda en la fecha actual.")
                return redirect('caja:lista')
            
            # Create caja
            caja = Caja.objects.create(
                tienda_id=tienda_id,
                fecha=today,
                fondo_inicial=fondo_inicial,
                saldo_final=fondo_inicial,
                created_by=request.user
            )
            
            messages.success(request, f"Caja abierta con éxito. Fondo inicial: ${float(fondo_inicial):.2f}")
            return redirect('caja:lista')
            
        except Exception as e:
            messages.error(request, f"Error al abrir la caja: {str(e)}")
    
    context = {
        'tiendas': tiendas,
    }
    
    return render(request, 'caja/caja_form.html', context)

def cerrar_caja(request, pk):
    """Vista para cerrar una caja"""
    caja = get_object_or_404(Caja, pk=pk, cerrada=False)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Calculate totals
                total_ingresos = caja.transacciones.filter(tipo_movimiento='INGRESO').aggregate(Sum('monto'))['monto__sum'] or 0
                total_egresos = caja.transacciones.filter(tipo_movimiento='EGRESO').aggregate(Sum('monto'))['monto__sum'] or 0
                
                # Update caja
                caja.ingresos = total_ingresos
                caja.egresos = total_egresos
                caja.saldo_final = caja.fondo_inicial + total_ingresos - total_egresos
                caja.cerrada = True
                caja.updated_by = request.user
                caja.save()
                
                messages.success(request, f"Caja cerrada con éxito. Saldo final: ${float(caja.saldo_final):.2f}")
                return redirect('caja:lista')
        
        except Exception as e:
            messages.error(request, f"Error al cerrar la caja: {str(e)}")
    
    # Calculate current totals for display    total_ingresos = caja.transacciones.filter(tipo_movimiento='INGRESO').aggregate(Sum('monto'))['monto__sum'] or 0
    total_egresos = caja.transacciones.filter(tipo_movimiento='EGRESO').aggregate(Sum('monto'))['monto__sum'] or 0
    saldo_actual = caja.fondo_inicial + total_ingresos - total_egresos
    
    # Get transactions
    transacciones = caja.transacciones.select_related('pedido', 'anticipo', 'nota_cargo', 'created_by').order_by('-created_at')
    
    context = {
        'caja': caja,
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'saldo_actual': saldo_actual,
        'transacciones': transacciones,
    }
    
    return render(request, 'caja/caja_cierre.html', context)

def movimientos_list(request):
    """Vista para listar movimientos de caja"""
    # Get filter parameters
    fecha_desde = request.GET.get('fecha_desde', date.today().isoformat())
    fecha_hasta = request.GET.get('fecha_hasta', date.today().isoformat())
    tienda_id = request.GET.get('tienda', '')
    tipo_movimiento = request.GET.get('tipo', '')
    
    # Base query
    movimientos = TransaccionCaja.objects.select_related('caja', 'caja__tienda', 'pedido', 'anticipo', 'nota_cargo', 'created_by')
      # Apply filters
    if fecha_desde:
        fecha_desde_obj = datetime.fromisoformat(fecha_desde).date()
        movimientos = movimientos.filter(caja__fecha__gte=fecha_desde_obj)
    
    if fecha_hasta:
        fecha_hasta_obj = datetime.fromisoformat(fecha_hasta).date()
        movimientos = movimientos.filter(caja__fecha__lte=fecha_hasta_obj)
    
    if tienda_id:
        movimientos = movimientos.filter(caja__tienda_id=tienda_id)
    
    if tipo_movimiento:
        # Convert to uppercase to match our model choices
        tipo_movimiento_upper = tipo_movimiento.upper()
        movimientos = movimientos.filter(tipo_movimiento=tipo_movimiento_upper)
    
    # Get tiendas for filter dropdown
    tiendas = Tienda.objects.all()
    
    # Calculate totals for summary
    total_ingresos = movimientos.filter(tipo_movimiento='INGRESO').aggregate(Sum('monto'))['monto__sum'] or 0
    total_egresos = movimientos.filter(tipo_movimiento='EGRESO').aggregate(Sum('monto'))['monto__sum'] or 0
    saldo_neto = total_ingresos - total_egresos
    
    context = {
        'movimientos': movimientos,
        'tiendas': tiendas,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'tienda_seleccionada': tienda_id,
        'tipo_movimiento': tipo_movimiento,
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'saldo_neto': saldo_neto,
    }
    
    return render(request, 'caja/movimientos_list.html', context)

def nota_cargo_create(request):
    """Vista para crear una nueva nota de cargo"""
    # Get open cash registers
    today = date.today()
    cajas_abiertas = Caja.objects.filter(fecha=today, cerrada=False).select_related('tienda')
    
    if request.method == 'POST':
        try:
            # Get form data
            caja_id = request.POST.get('caja')
            monto = request.POST.get('monto', 0)
            motivo = request.POST.get('motivo', '').strip()
            
            # Validate data
            if not caja_id or not motivo:
                messages.error(request, "Caja y motivo son obligatorios.")
                return redirect('caja:nueva_nota_cargo')
            
            if float(monto) <= 0:
                messages.error(request, "El monto debe ser mayor a cero.")
                return redirect('caja:nueva_nota_cargo')
            
            # Get caja
            caja = get_object_or_404(Caja, pk=caja_id, cerrada=False)
            
            with transaction.atomic():
                # Create nota de cargo
                nota_cargo = NotaCargo.objects.create(
                    caja=caja,
                    monto=monto,
                    motivo=motivo,
                    fecha=today,
                    created_by=request.user
                )
                
                # Create transaction
                TransaccionCaja.objects.create(
                    caja=caja,
                    tipo_movimiento='egreso',
                    monto=monto,
                    descripcion=f'Nota de Cargo: {motivo}',
                    nota_cargo=nota_cargo,
                    created_by=request.user
                )
            
            messages.success(request, f"Nota de cargo por ${float(monto):.2f} registrada correctamente.")
            return redirect('caja:movimientos')
            
        except Exception as e:
            messages.error(request, f"Error al registrar la nota de cargo: {str(e)}")
    
    context = {
        'cajas_abiertas': cajas_abiertas,
    }
    
    return render(request, 'caja/nota_cargo_form.html', context)

def factura_list(request):
    """Vista para listar facturas"""
    # Get filter parameters
    fecha_desde = request.GET.get('fecha_desde', (date.today().replace(day=1)).isoformat())
    fecha_hasta = request.GET.get('fecha_hasta', date.today().isoformat())
    folio = request.GET.get('folio', '')
    
    # Base query
    facturas = Factura.objects.select_related('pedido__cliente', 'created_by')
    
    # Apply filters
    if fecha_desde:
        try:
            fecha_desde_obj = datetime.fromisoformat(fecha_desde).date()
            facturas = facturas.filter(fecha__gte=fecha_desde_obj)
        except ValueError:
            messages.error(request, "Formato de fecha inicial inválido.")
    
    if fecha_hasta:
        try:
            fecha_hasta_obj = datetime.fromisoformat(fecha_hasta).date()
            facturas = facturas.filter(fecha__lte=fecha_hasta_obj)
        except ValueError:
            messages.error(request, "Formato de fecha final inválido.")
    
    if folio:
        facturas = facturas.filter(folio__icontains=folio)
    
    # Calculate total for summary
    total_facturado = facturas.aggregate(Sum('total'))['total__sum'] or 0
    
    # Calculate promedio si hay facturas
    promedio_factura = 0
    if facturas.count() > 0:
        promedio_factura = total_facturado / facturas.count()
    
    context = {
        'facturas': facturas,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'folio': folio,
        'total_facturado': total_facturado,
        'promedio_factura': promedio_factura,
    }
    
    return render(request, 'caja/factura_list.html', context)

def reporte_caja(request):
    """Vista para generar reportes de caja"""
    # Get filter parameters
    fecha_desde = request.GET.get('fecha_desde', (date.today().replace(day=1)).isoformat())
    fecha_hasta = request.GET.get('fecha_hasta', date.today().isoformat())
    tienda_id = request.GET.get('tienda', '')
    
    # Base query
    cajas = Caja.objects.select_related('tienda')
    
    # Apply filters
    if fecha_desde:
        fecha_desde_obj = datetime.fromisoformat(fecha_desde).date()
        cajas = cajas.filter(fecha__gte=fecha_desde_obj)
    
    if fecha_hasta:
        fecha_hasta_obj = datetime.fromisoformat(fecha_hasta).date()
        cajas = cajas.filter(fecha__lte=fecha_hasta_obj)
    
    if tienda_id:
        cajas = cajas.filter(tienda_id=tienda_id)
    
    # Get tiendas for filter dropdown
    tiendas = Tienda.objects.all()
    
    # Calculate summary statistics
    total_ingresos = cajas.aggregate(Sum('ingresos'))['ingresos__sum'] or 0
    total_egresos = cajas.aggregate(Sum('egresos'))['egresos__sum'] or 0
    total_saldo = cajas.filter(cerrada=True).aggregate(Sum('saldo_final'))['saldo_final__sum'] or 0
    
    # Group cajas by tienda for visualization
    tiendas_data = {}
    for caja in cajas:
        tienda_id = caja.tienda.id
        if tienda_id not in tiendas_data:
            tiendas_data[tienda_id] = {
                'nombre': caja.tienda.nombre,
                'ingresos': 0,
                'egresos': 0,
                'saldo': 0,
                'cajas_count': 0
            }
        
        tiendas_data[tienda_id]['ingresos'] += caja.ingresos
        tiendas_data[tienda_id]['egresos'] += caja.egresos
        if caja.cerrada:
            tiendas_data[tienda_id]['saldo'] += caja.saldo_final
        tiendas_data[tienda_id]['cajas_count'] += 1
    
    context = {
        'cajas': cajas,
        'tiendas': tiendas,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'tienda_seleccionada': tienda_id,
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'total_saldo': total_saldo,
        'tiendas_data': tiendas_data,
    }
    
    return render(request, 'caja/reporte.html', context)

# API viewsets
@extend_schema(tags=["Caja"])
class CajaViewSet(viewsets.ModelViewSet):
    queryset = Caja.objects.all()
    serializer_class = CajaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tienda', 'fecha', 'ingresos', 'egresos', 'saldo_final', 'cerrada']

    @extend_schema(
        description="Abre la caja diaria para una tienda con un fondo inicial.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'tienda_id': {'type': 'integer', 'description': 'ID de la tienda'},
                    'fondo_inicial': {'type': 'number', 'description': 'Monto del fondo inicial'},
                },
                'required': ['tienda_id', 'fondo_inicial']
            }
        },
        responses={201: CajaSerializer, 400: OpenApiTypes.OBJECT, 409: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['post'])
    def abrir_caja(self, request):
        tienda_id = request.data.get('tienda_id')
        fondo_inicial = request.data.get('fondo_inicial')
        today = date.today()

        if not tienda_id or fondo_inicial is None:
            return Response({"error": "Debe proporcionar el ID de la tienda y el fondo inicial."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tienda = Tienda.objects.get(id=tienda_id)
        except Tienda.DoesNotExist:
            return Response({"error": "Tienda no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        if Caja.objects.filter(tienda=tienda, fecha=today, cerrada=False).exists():
            return Response({"error": "Ya existe una caja abierta para esta tienda en la fecha actual."}, status=status.HTTP_409_CONFLICT)

        with transaction.atomic():
            caja = Caja.objects.create(
                tienda=tienda,
                fecha=today,
                fondo_inicial=fondo_inicial,
                saldo_final=fondo_inicial,
                created_by=request.user
            )

        serializer = self.get_serializer(caja)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        description="Cierra la caja diaria para una tienda, calcula el saldo final y genera el reporte.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'tienda_id': {'type': 'integer', 'description': 'ID de la tienda'},
                    'fecha': {'type': 'string', 'format': 'date', 'description': 'Fecha de la caja a cerrar (YYYY-MM-DD)'},
                },
                'required': ['tienda_id', 'fecha']
            }
        },
        responses={200: CajaSerializer, 400: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['post'])
    def cerrar_caja(self, request):
        tienda_id = request.data.get('tienda_id')
        fecha_str = request.data.get('fecha')

        if not tienda_id or not fecha_str:
             return Response({"error": "Debe proporcionar el ID de la tienda y la fecha."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            fecha = date.fromisoformat(fecha_str)
        except ValueError:
            return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            caja = Caja.objects.select_for_update().get(tienda_id=tienda_id, fecha=fecha, cerrada=False)
        except Caja.DoesNotExist:
            return Response({"error": "Caja no encontrada o ya cerrada para esta tienda y fecha."}, status=status.HTTP_404_NOT_FOUND)
        
        with transaction.atomic():
            total_ingresos = caja.transacciones.filter(tipo_movimiento='INGRESO').aggregate(Sum('monto'))['monto__sum'] or 0
            total_egresos = caja.transacciones.filter(tipo_movimiento='EGRESO').aggregate(Sum('monto'))['monto__sum'] or 0

            caja.ingresos = total_ingresos
            caja.egresos = total_egresos
            caja.saldo_final = caja.fondo_inicial + total_ingresos - total_egresos
            caja.cerrada = True
            caja.save()

        serializer = self.get_serializer(caja)
        return Response(serializer.data)

@extend_schema(tags=["Caja"])
class NotaCargoViewSet(viewsets.ModelViewSet):
    queryset = NotaCargo.objects.all()
    serializer_class = NotaCargoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['caja', 'fecha', 'monto', 'motivo']

    def perform_create(self, serializer):
        # Save the NotaCargo
        nota_cargo = serializer.save(created_by=self.request.user)

        # Record the transaction in the cash register
        # The caja is already linked to the NotaCargo during creation
        user = self.request.user

        # Create TransaccionCaja entry for the expense
        TransaccionCaja.objects.create(
            caja=nota_cargo.caja,
            tipo_movimiento='egreso',
            monto=nota_cargo.monto,
            descripcion=f'Nota de Cargo #{nota_cargo.id}: {nota_cargo.motivo}',
            nota_cargo=nota_cargo, # Link to the NotaCargo record
            created_by=user
        )

@extend_schema(tags=["Caja"])
class FacturaViewSet(viewsets.ModelViewSet):
    queryset = Factura.objects.all()
    serializer_class = FacturaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['pedido', 'folio', 'fecha', 'total']

@extend_schema(tags=["Caja"])
class TransaccionCajaViewSet(viewsets.ModelViewSet):
    queryset = TransaccionCaja.objects.all()
    serializer_class = TransaccionCajaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['caja', 'tipo_movimiento', 'pedido', 'anticipo', 'nota_cargo', 'created_at']
    
    def perform_create(self, serializer):
        user = self.request.user
        today = date.today()

        # Get the tienda from the request data or find available open caja
        # In DRF, request.data contains the POST data
        tienda_id = None
        if hasattr(self.request, 'data') and self.request.data:
            tienda_id = self.request.data.get('tienda_id')
        elif hasattr(self.request, 'POST'):
            # Fallback to request.POST for form data
            tienda_id = self.request.POST.get('tienda_id')
        
        if tienda_id:
            try:
                caja_abierta = Caja.objects.get(tienda_id=tienda_id, fecha=today, cerrada=False)
            except Caja.DoesNotExist:
                raise ValidationError("No hay una caja abierta para la tienda especificada en la fecha actual.")
        else:
            # If no tienda specified, try to find any open caja for today
            try:
                caja_abierta = Caja.objects.filter(fecha=today, cerrada=False).first()
                if not caja_abierta:
                    raise ValidationError("No hay cajas abiertas en la fecha actual.")
            except Exception:
                raise ValidationError("No hay una caja abierta en la fecha actual.")

        serializer.save(created_by=user, caja=caja_abierta)

class MovimientosCajaReporteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    """
    Devuelve un reporte de movimientos de caja agrupados por tienda y fecha.
    """
    @extend_schema(
        parameters=[
            OpenApiParameter("tienda_id", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description="Filtrar por ID de tienda"),
            OpenApiParameter("fecha", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False, description="Filtrar por fecha (YYYY-MM-DD)"),
        ],
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        tienda_id = request.query_params.get("tienda_id")
        fecha_str = request.query_params.get("fecha")

        cajas_queryset = Caja.objects.select_related('tienda', 'created_by').all()

        if tienda_id:
            cajas_queryset = cajas_queryset.filter(tienda_id=tienda_id)
        if fecha_str:
            try:
                fecha = date.fromisoformat(fecha_str)
                cajas_queryset = cajas_queryset.filter(fecha=fecha)
            except ValueError:
                return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        data = []
        for caja in cajas_queryset:
            movimientos = []

            # Get all transactions for this cash box
            transacciones = caja.transacciones.select_related('created_by', 'pedido', 'anticipo', 'nota_cargo').all()

            for transaccion in transacciones:
                descripcion = transaccion.descripcion
                # Enhance description based on linked object
                if transaccion.pedido:
                    descripcion = f"Venta Pedido #{transaccion.pedido.id}"
                elif transaccion.anticipo:
                    descripcion = f"Anticipo Cliente #{transaccion.anticipo.cliente.id}"
                elif transaccion.nota_cargo:
                     descripcion = f"Nota de Cargo #{transaccion.nota_cargo.id}: {transaccion.nota_cargo.motivo}"

                movimientos.append({
                    'tipo': transaccion.tipo_movimiento,
                    'monto': transaccion.monto,
                    'usuario': transaccion.created_by.username if transaccion.created_by else None,
                    'descripcion': descripcion,
                    'created_at': transaccion.created_at
                })

            data.append({
                'tienda_id': caja.tienda.id,
                'tienda_nombre': caja.tienda.nombre,
                'fecha': caja.fecha,
                'fondo_inicial': caja.fondo_inicial,
                'ingresos_totales': caja.ingresos,
                'egresos_totales': caja.egresos,
                'saldo_final': caja.saldo_final,
                'movimientos': movimientos
            })

        return Response(data)

def factura_create(request):
    """Vista para crear una nueva factura"""
    pedidos_sin_factura = Pedido.objects.filter(
        estado='surtido', 
        pagado=True,
        factura__isnull=True  # Asegurarse que no tengan factura ya generada
    ).select_related('cliente', 'tienda').order_by('-fecha')
    if request.method == 'POST':
        pedido_id = request.POST.get('pedido')
        folio = request.POST.get('folio')
        fecha = request.POST.get('fecha')
        total = request.POST.get('total')
        
        # Validaciones
        if not pedido_id or not folio or not fecha or not total:
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect('caja:nueva_factura')
        
        try:
            pedido = Pedido.objects.get(id=pedido_id)
            
            # Verificar que el pedido no tenga ya una factura
            if hasattr(pedido, 'factura'):
                messages.error(request, f"El pedido #{pedido_id} ya tiene una factura asociada.")
                return redirect('caja:facturas')
            
            # Verificar que el pedido esté pagado y surtido
            if not pedido.pagado or pedido.estado != 'surtido':
                messages.error(request, f"El pedido #{pedido_id} no puede facturarse porque no está pagado o surtido.")
                return redirect('caja:nueva_factura')
                
            # Crear la factura
            factura = Factura.objects.create(
                pedido=pedido,
                folio=folio,
                fecha=fecha,
                total=float(total),
                created_by=request.user
            )
            
            messages.success(request, f"Factura #{folio} generada con éxito.")
            return redirect('caja:ver_factura', factura.id)
            
        except Pedido.DoesNotExist:
            messages.error(request, f"El pedido #{pedido_id} no existe.")
        except IntegrityError:
            messages.error(request, f"Ya existe una factura con el folio {folio}.")
            # Recargar la página con los datos para que el usuario pueda corregir
            context = {
                'pedidos_sin_factura': pedidos_sin_factura,
                'pedido_id': pedido_id,
                'folio': folio,
                'fecha': fecha,
                'total': total
            }
            return render(request, 'caja/factura_form.html', context)
        except Exception as e:
            messages.error(request, f"Error al generar la factura: {str(e)}")
    
    context = {
        'pedidos_sin_factura': pedidos_sin_factura,
    }
    
    return render(request, 'caja/factura_form.html', context)

def factura_detail(request, pk):
    """Vista para ver detalle de una factura"""
    factura = get_object_or_404(Factura.objects.select_related(
        'pedido__cliente', 'pedido__tienda', 'created_by'
    ), pk=pk)
    
    # Calcular subtotal y descuento
    detalles = factura.pedido.detalles.all()
    subtotal = sum(detalle.subtotal for detalle in detalles)
    
    descuento = 0
    if factura.pedido.descuento_aplicado > 0:
        descuento = subtotal * (factura.pedido.descuento_aplicado / 100)
    
    context = {
        'factura': factura,
        'subtotal': subtotal,
        'descuento': descuento,
    }
    
    return render(request, 'caja/factura_detail.html', context)

def factura_print(request, pk):
    """Vista para imprimir una factura"""
    factura = get_object_or_404(Factura.objects.select_related(
        'pedido__cliente', 'pedido__tienda', 'created_by'
    ), pk=pk)
    
    # Calcular subtotal y descuento
    detalles = factura.pedido.detalles.all()
    subtotal = sum(detalle.subtotal for detalle in detalles)
    
    descuento = 0
    if factura.pedido.descuento_aplicado > 0:
        descuento = subtotal * (factura.pedido.descuento_aplicado / 100)
    
    context = {
        'factura': factura,
        'subtotal': subtotal,
        'descuento': descuento,
    }
    
    return render(request, 'caja/factura_print.html', context)

def factura_pdf(request, pk):
    """Vista para generar PDF de una factura"""
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    
    factura = get_object_or_404(Factura.objects.select_related(
        'pedido__cliente', 'pedido__tienda', 'created_by'
    ), pk=pk)
    
    # Calcular subtotal y descuento
    detalles = factura.pedido.detalles.all()
    subtotal = sum(detalle.subtotal for detalle in detalles)
    
    descuento = 0
    if factura.pedido.descuento_aplicado > 0:
        descuento = subtotal * (factura.pedido.descuento_aplicado / 100)
    
    context = {
        'factura': factura,
        'subtotal': subtotal,
        'descuento': descuento,
        'detalles': detalles,
    }
    
    # En una implementación real se utilizaría una biblioteca como WeasyPrint, 
    # ReportLab o xhtml2pdf para generar un PDF. En este ejemplo usamos
    # una solución simplificada basada en el navegador.
    
    # 1. Generar el HTML para el PDF
    html_string = render_to_string('caja/factura_print.html', context)
    
    # 2. Configurar la respuesta HTTP
    response = HttpResponse(content_type='text/html')
    response['Content-Disposition'] = f'attachment; filename="factura_{factura.folio}.html"'
    
    # 3. Escribir el HTML en la respuesta
    response.write(html_string)
    
    messages.success(request, f"Factura #{factura.folio} descargada correctamente.")
    return response
