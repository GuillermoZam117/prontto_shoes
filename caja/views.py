from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Caja, NotaCargo, Factura, TransaccionCaja
from .serializers import CajaSerializer, NotaCargoSerializer, FacturaSerializer, TransaccionCajaSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from datetime import date
from django.contrib.auth import get_user_model
from tiendas.models import Tienda

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
            total_ingresos = caja.transacciones.filter(tipo_movimiento='ingreso').aggregate(Sum('monto'))['monto__sum'] or 0
            total_egresos = caja.transacciones.filter(tipo_movimiento='egreso').aggregate(Sum('monto'))['monto__sum'] or 0

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

        if not hasattr(user, 'tienda') or user.tienda is None:
             raise ValidationError("User is not associated with a store.")
             
        try:
            caja_abierta = Caja.objects.get(tienda=user.tienda, fecha=today, cerrada=False)
        except Caja.DoesNotExist:
             raise ValidationError("No hay una caja abierta para su tienda en la fecha actual.")

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
