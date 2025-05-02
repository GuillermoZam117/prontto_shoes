from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Cliente, Anticipo, DescuentoCliente
from .serializers import ClienteSerializer, AnticipoSerializer, DescuentoClienteSerializer
from django_filters.rest_framework import DjangoFilterBackend
# Mejora Swagger:
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.dateparse import parse_date
from ventas.models import Pedido

@extend_schema(tags=["Clientes"])
class ClienteViewSet(viewsets.ModelViewSet):
    """
    Gestiona el alta, consulta, edición y filtrado de clientes.
    """
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['nombre', 'contacto', 'saldo_a_favor', 'tienda']

    @swagger_auto_schema(
        operation_description="Crea un nuevo cliente.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'nombre': openapi.Schema(type=openapi.TYPE_STRING, description='Nombre del cliente', example='Zapatería El Paso'),
                'contacto': openapi.Schema(type=openapi.TYPE_STRING, description='Contacto', example='Juan Pérez'),
                'observaciones': openapi.Schema(type=openapi.TYPE_STRING, description='Observaciones', example='Cliente frecuente'),
                'saldo_a_favor': openapi.Schema(type=openapi.TYPE_NUMBER, description='Saldo a favor', example=0),
                'tienda': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID de tienda', example=1),
            },
            required=['nombre', 'tienda']
        ),
        responses={201: ClienteSerializer}
    )
    def create(self, request, *args, **kwargs):
        """Crea un cliente nuevo y lo retorna."""
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Reporte: Clientes sin movimientos (compras) en un periodo determinado. Parámetros: fecha_inicio, fecha_fin (YYYY-MM-DD)",
        manual_parameters=[
            openapi.Parameter('fecha_inicio', openapi.IN_QUERY, description="Fecha de inicio (YYYY-MM-DD)", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('fecha_fin', openapi.IN_QUERY, description="Fecha de fin (YYYY-MM-DD)", type=openapi.TYPE_STRING, required=True),
        ],
        responses={200: ClienteSerializer(many=True)}
    )
    @action(detail=False, methods=["get"], url_path="sin_movimientos")
    def clientes_sin_movimientos(self, request):
        """
        Reporte: Clientes sin movimientos (compras) en un periodo determinado.
        Parámetros: fecha_inicio, fecha_fin (YYYY-MM-DD)
        Devuelve los clientes que no han realizado pedidos en el rango de fechas indicado.
        """
        fecha_inicio = request.query_params.get("fecha_inicio")
        fecha_fin = request.query_params.get("fecha_fin")
        if not fecha_inicio or not fecha_fin:
            return Response({"error": "Debe proporcionar fecha_inicio y fecha_fin en formato YYYY-MM-DD."}, status=400)
        try:
            fecha_inicio = parse_date(fecha_inicio)
            fecha_fin = parse_date(fecha_fin)
        except Exception:
            return Response({"error": "Formato de fecha inválido."}, status=400)
        if not fecha_inicio or not fecha_fin:
            return Response({"error": "Formato de fecha inválido."}, status=400)
        # IDs de clientes con pedidos en el rango
        clientes_con_pedidos = Pedido.objects.filter(
            fecha__date__gte=fecha_inicio,
            fecha__date__lte=fecha_fin
        ).values_list("cliente_id", flat=True).distinct()
        # Clientes sin pedidos en el rango
        clientes_sin = Cliente.objects.exclude(id__in=clientes_con_pedidos)
        page = self.paginate_queryset(clientes_sin)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(clientes_sin, many=True)
        return Response(serializer.data)

@extend_schema(tags=["DescuentosClientes"])
class DescuentoClienteViewSet(viewsets.ModelViewSet):
    """
    Gestiona descuentos aplicados a clientes.
    """
    queryset = DescuentoCliente.objects.all()
    serializer_class = DescuentoClienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cliente', 'mes_vigente', 'porcentaje']
