from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from django.utils.dateparse import parse_date
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from .models import Devolucion
from .serializers import DevolucionSerializer

class DevolucionViewSet(viewsets.ModelViewSet):
    queryset = Devolucion.objects.all()
    serializer_class = DevolucionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cliente', 'producto', 'tipo', 'fecha', 'estado', 'confirmacion_proveedor', 'afecta_inventario']

@extend_schema(
    tags=["Reportes"],
    parameters=[
        OpenApiParameter("cliente_id", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description="Filtrar por ID de cliente"),
        OpenApiParameter("fecha_desde", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False, description="Filtrar devoluciones desde esta fecha (YYYY-MM-DD)"),
        OpenApiParameter("fecha_hasta", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False, description="Filtrar devoluciones hasta esta fecha (YYYY-MM-DD)"),
        OpenApiParameter("tipo", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False, description="Filtrar por tipo de devolución (defecto/cambio)"),
        OpenApiParameter("estado", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False, description="Filtrar por estado de validación"),
        OpenApiParameter("limit", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description="Límite de resultados por página"),
        OpenApiParameter("offset", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description="Offset para paginación"),
    ],
    description="Devuelve un reporte de devoluciones por cliente. Permite filtrar por cliente, fechas, tipo y estado. Incluye detalles del producto y estado de validación."
)
class DevolucionesReporteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination

    def get(self, request):
        # Obtener y validar parámetros
        cliente_id = request.query_params.get("cliente_id")
        fecha_desde = request.query_params.get("fecha_desde")
        fecha_hasta = request.query_params.get("fecha_hasta")
        tipo = request.query_params.get("tipo")
        estado = request.query_params.get("estado")

        # Construir query base
        devoluciones = Devolucion.objects.select_related(
            'cliente', 
            'producto', 
            'producto__proveedor'
        ).all()

        # Aplicar filtros
        if cliente_id:
            devoluciones = devoluciones.filter(cliente_id=cliente_id)
        if fecha_desde:
            devoluciones = devoluciones.filter(fecha__gte=parse_date(fecha_desde))
        if fecha_hasta:
            devoluciones = devoluciones.filter(fecha__lte=parse_date(fecha_hasta))
        if tipo:
            devoluciones = devoluciones.filter(tipo=tipo)
        if estado:
            devoluciones = devoluciones.filter(estado=estado)

        # Agrupar por cliente para el reporte
        data = []
        clientes_procesados = {}

        for dev in devoluciones:
            cliente_id = dev.cliente.id
            
            if cliente_id not in clientes_procesados:
                clientes_procesados[cliente_id] = {
                    'cliente_id': cliente_id,
                    'cliente_nombre': dev.cliente.nombre,
                    'total_devoluciones': 0,
                    'saldo_a_favor_total': 0,
                    'devoluciones': []
                }

            # Agregar detalles de la devolución
            clientes_procesados[cliente_id]['devoluciones'].append({
                'devolucion_id': dev.id,
                'fecha': dev.fecha,
                'producto': {
                    'id': dev.producto.id,
                    'codigo': dev.producto.codigo,
                    'marca': dev.producto.marca,
                    'modelo': dev.producto.modelo,
                    'color': dev.producto.color,
                    'propiedad': dev.producto.propiedad,
                    'proveedor': dev.producto.proveedor.nombre
                },
                'tipo': dev.tipo,
                'motivo': dev.motivo,
                'estado': dev.estado,
                'validacion': {
                    'confirmacion_proveedor': dev.confirmacion_proveedor,
                    'afecta_inventario': dev.afecta_inventario
                },
                'saldo_generado': float(dev.saldo_a_favor_generado)
            })

            # Actualizar totales del cliente
            clientes_procesados[cliente_id]['total_devoluciones'] += 1
            clientes_procesados[cliente_id]['saldo_a_favor_total'] += float(dev.saldo_a_favor_generado)

        # Convertir el diccionario a lista para la respuesta
        data = list(clientes_procesados.values())

        # Aplicar paginación
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(data, request)
        
        if page is not None:
            return paginator.get_paginated_response(page)
            
        return Response(data)
