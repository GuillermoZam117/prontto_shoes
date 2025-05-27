import time
import csv
import json
from io import StringIO
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db import models
from django.db.models import Q, Count, Sum, Avg, F, Max, Min
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import ReportePersonalizado, EjecucionReporte
from .serializers import (
    ReportePersonalizadoSerializer, 
    EjecucionReporteSerializer,
    ReporteEjecutarSerializer
)

# Importar modelos necesarios para los reportes
from clientes.models import Cliente
from productos.models import Producto
from inventario.models import Inventario, Traspaso
from ventas.models import Pedido, DetallePedido
from descuentos.models import TabuladorDescuento
from tiendas.models import Tienda
from devoluciones.models import Devolucion

@extend_schema(tags=["Reportes Personalizados"])
class ReportePersonalizadoViewSet(viewsets.ModelViewSet):
    queryset = ReportePersonalizado.objects.all()
    serializer_class = ReportePersonalizadoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tipo', 'activo', 'creado_por']
    
    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)

@extend_schema(tags=["Reportes Personalizados"])
class EjecucionReporteViewSet(viewsets.ModelViewSet):
    queryset = EjecucionReporte.objects.all()
    serializer_class = EjecucionReporteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['reporte', 'ejecutado_por', 'fecha_ejecucion']

class ReportesAvanzadosAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Reportes Avanzados"],
        parameters=[
            OpenApiParameter("tipo", OpenApiTypes.STR, OpenApiParameter.QUERY, required=True, 
                           description="Tipo de reporte a generar"),
            OpenApiParameter("fecha_desde", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("fecha_hasta", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("tienda_id", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("cliente_id", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("limite", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("formato", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False,
                           description="Formato de salida: json, csv, excel"),
        ],
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        """Ejecutar reportes avanzados dinámicamente"""
        serializer = ReporteEjecutarSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        tipo_reporte = data.get('tipo_reporte')
        
        start_time = time.time()
        
        try:
            if tipo_reporte == 'clientes_inactivos':
                resultado = self._generar_reporte_clientes_inactivos(data)
            elif tipo_reporte == 'historial_precios':
                resultado = self._generar_reporte_historial_precios(data)
            elif tipo_reporte == 'inventario_diario':
                resultado = self._generar_reporte_inventario_diario(data)
            elif tipo_reporte == 'descuentos_mensuales':
                resultado = self._generar_reporte_descuentos_mensuales(data)
            elif tipo_reporte == 'cumplimiento_metas':
                resultado = self._generar_reporte_cumplimiento_metas(data)
            elif tipo_reporte == 'ventas_por_vendedor':
                resultado = self._generar_reporte_ventas_vendedor(data)
            elif tipo_reporte == 'productos_mas_vendidos':
                resultado = self._generar_reporte_productos_vendidos(data)
            elif tipo_reporte == 'analisis_rentabilidad':
                resultado = self._generar_reporte_rentabilidad(data)
            elif tipo_reporte == 'stock_critico':
                resultado = self._generar_reporte_stock_critico(data)
            elif tipo_reporte == 'tendencias_ventas':
                resultado = self._generar_reporte_tendencias_ventas(data)
            else:
                return Response(
                    {"error": f"Tipo de reporte no soportado: {tipo_reporte}"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            execution_time = time.time() - start_time
            
            # Registrar ejecución si se especifica un reporte personalizado
            if 'reporte_id' in data:
                self._registrar_ejecucion(data['reporte_id'], data, execution_time, len(resultado['datos']))
            
            # Formatear respuesta según el formato solicitado
            formato = data.get('formato_salida', 'json')
            if formato == 'csv':
                return self._generar_csv_response(resultado, tipo_reporte)
            elif formato == 'excel':
                return self._generar_excel_response(resultado, tipo_reporte)
            else:
                resultado['metadatos'] = {
                    'tiempo_ejecucion': round(execution_time, 2),
                    'total_registros': len(resultado['datos']),
                    'fecha_generacion': timezone.now().isoformat(),
                    'parametros': data
                }
                return Response(resultado)
                
        except Exception as e:
            return Response(
                {"error": f"Error al generar reporte: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _generar_reporte_clientes_inactivos(self, parametros):
        """Generar reporte de clientes sin movimientos"""
        fecha_desde = parametros.get('fecha_desde', timezone.now().date() - timedelta(days=90))
        fecha_hasta = parametros.get('fecha_hasta', timezone.now().date())
        limite = parametros.get('limite_registros', 1000)
        dias_inactividad = parametros.get('dias_inactividad', 30)
        
        # Obtener clientes que NO tienen pedidos en el período
        clientes_con_pedidos = Pedido.objects.filter(
            fecha__date__range=[fecha_desde, fecha_hasta]
        ).values_list('cliente_id', flat=True).distinct()
        
        clientes_inactivos = Cliente.objects.exclude(
            id__in=clientes_con_pedidos
        ).select_related('tienda')[:limite]
        
        datos = []
        for cliente in clientes_inactivos:
            # Get last order and order statistics
            ultimo_pedido = Pedido.objects.filter(cliente=cliente).order_by('-fecha').first()
            pedidos_count = Pedido.objects.filter(cliente=cliente).count()
            total_gastado = Pedido.objects.filter(cliente=cliente, pagado=True).aggregate(
                total=models.Sum('total')
            )['total']
            
            # Check if client meets inactivity criteria
            if dias_inactividad and ultimo_pedido:
                days_inactive = (timezone.now().date() - ultimo_pedido.fecha.date()).days
                if days_inactive < dias_inactividad:
                    continue  # Skip clients who are not inactive enough
            
            datos.append({
                'cliente_id': cliente.id,
                'cliente_nombre': cliente.nombre,
                'contacto': cliente.contacto,
                'observaciones': cliente.observaciones,
                'ultimo_pedido': ultimo_pedido.fecha.date() if ultimo_pedido else None,
                'total_pedidos_historico': pedidos_count,
                'total_gastado_historico': float(total_gastado or 0),
                'saldo_a_favor': float(cliente.saldo_a_favor),
                'dias_inactivo': (timezone.now().date() - ultimo_pedido.fecha.date()).days if ultimo_pedido else None
            })
        
        return {
            'titulo': 'Clientes sin Movimientos',
            'periodo': f"{fecha_desde} a {fecha_hasta}",
            'datos': datos,
            'resumen': {
                'total_clientes_inactivos': len(datos),
                'periodo_analizado_dias': (fecha_hasta - fecha_desde).days
            }
        }

    def _generar_reporte_historial_precios(self, parametros):
        """Generar reporte de historial de cambios de precios"""
        fecha_desde = parametros.get('fecha_desde')
        fecha_hasta = parametros.get('fecha_hasta')
        producto_id = parametros.get('producto_id')
        limite = parametros.get('limite_registros', 1000)
        
        # Como no existe modelo PrecioProducto, usar productos modificados recientemente
        query = Producto.objects.select_related('tienda', 'proveedor').all()
        
        if fecha_desde:
            query = query.filter(updated_at__gte=fecha_desde)
        if fecha_hasta:
            query = query.filter(updated_at__lte=fecha_hasta)
        if producto_id:
            query = query.filter(id=producto_id)
        
        productos_modificados = query.order_by('-updated_at')[:limite]
        
        datos = []
        for producto in productos_modificados:
            # Calcular margen de ganancia
            margen = ((producto.precio - producto.costo) / producto.precio * 100) if producto.precio > 0 else 0
            
            datos.append({
                'producto_id': producto.id,
                'producto_codigo': producto.codigo,
                'producto_nombre': str(producto),
                'precio_actual': float(producto.precio),
                'costo_actual': float(producto.costo),
                'margen_ganancia': round(margen, 2),
                'fecha_modificacion': producto.updated_at.date(),
                'tienda': producto.tienda.nombre,
                'proveedor': producto.proveedor.nombre,
                'modificado_por': producto.updated_by.username if producto.updated_by else 'Sistema'
            })
        
        return {
            'titulo': 'Historial de Modificaciones de Productos',
            'datos': datos,
            'resumen': {
                'total_modificaciones': len(datos),
                'productos_afectados': len(set([d['producto_id'] for d in datos]))
            }
        }

    def _generar_reporte_inventario_diario(self, parametros):
        """Generar reporte de inventario diario y traspasos"""
        fecha_desde = parametros.get('fecha_desde', timezone.now().date())
        fecha_hasta = parametros.get('fecha_hasta', timezone.now().date())
        tienda_id = parametros.get('tienda_id')
        
        query = Inventario.objects.select_related('tienda', 'producto').all()
        
        if tienda_id:
            query = query.filter(tienda_id=tienda_id)
        
        inventarios = query.filter(
            fecha_registro__range=[fecha_desde, fecha_hasta]
        )
        
        # Obtener traspasos del período
        traspasos = Traspaso.objects.filter(
            fecha__date__range=[fecha_desde, fecha_hasta]
        ).select_related('tienda_origen', 'tienda_destino')
        
        datos_inventario = []
        for inv in inventarios:
            datos_inventario.append({
                'tienda_id': inv.tienda.id,
                'tienda_nombre': inv.tienda.nombre,
                'producto_id': inv.producto.id,
                'producto_codigo': inv.producto.codigo,
                'producto_nombre': str(inv.producto),
                'cantidad_actual': inv.cantidad_actual,
                'estado_stock': 'crítico' if inv.cantidad_actual <= 5 else 'normal',
                'fecha_registro': inv.fecha_registro
            })
        
        datos_traspasos = []
        for traspaso in traspasos:
            datos_traspasos.append({
                'id': traspaso.id,
                'tienda_origen': traspaso.tienda_origen.nombre,
                'tienda_destino': traspaso.tienda_destino.nombre,
                'fecha': traspaso.fecha.date(),
                'estado': traspaso.estado,
                'producto': str(traspaso.producto),
                'cantidad': traspaso.cantidad
            })
        
        return {
            'titulo': 'Inventario Diario y Traspasos',
            'periodo': f"{fecha_desde} a {fecha_hasta}",
            'inventario': datos_inventario,
            'traspasos': datos_traspasos,
            'resumen': {
                'total_productos_inventario': len(datos_inventario),
                'total_traspasos': len(datos_traspasos),
                'productos_stock_critico': len([d for d in datos_inventario if d['estado_stock'] == 'crítico'])
            }
        }
    
    def _generar_reporte_descuentos_mensuales(self, parametros):
        """Generar reporte de descuentos aplicados por mes"""
        fecha_desde = parametros.get('fecha_desde', timezone.now().date().replace(day=1))
        fecha_hasta = parametros.get('fecha_hasta', timezone.now().date())
        
        # Obtener pedidos con descuentos aplicados
        pedidos = Pedido.objects.filter(
            fecha__date__range=[fecha_desde, fecha_hasta],
            descuento_aplicado__gt=0
        ).select_related('cliente')
        
        # Agrupar por mes
        descuentos_mensuales = {}
        for pedido in pedidos:
            mes_key = f"{pedido.fecha.year}-{pedido.fecha.month:02d}"
            if mes_key not in descuentos_mensuales:
                descuentos_mensuales[mes_key] = {
                    'mes': mes_key,
                    'total_descuentos': 0,
                    'total_pedidos': 0,
                    'total_ventas': 0,
                    'porcentaje_descuento_promedio': 0
                }
            
            descuentos_mensuales[mes_key]['total_descuentos'] += float(pedido.descuento_aplicado)
            descuentos_mensuales[mes_key]['total_pedidos'] += 1
            descuentos_mensuales[mes_key]['total_ventas'] += float(pedido.total)
        
        # Calcular porcentajes
        datos = []
        for mes_data in descuentos_mensuales.values():
            if mes_data['total_ventas'] > 0:
                mes_data['porcentaje_descuento_promedio'] = round(
                    (mes_data['total_descuentos'] / mes_data['total_ventas']) * 100, 2
                )
            datos.append(mes_data)
        
        return {
            'titulo': 'Descuentos Aplicados por Mes',
            'periodo': f"{fecha_desde} a {fecha_hasta}",
            'datos': sorted(datos, key=lambda x: x['mes']),
            'resumen': {
                'total_descuentos_periodo': sum([d['total_descuentos'] for d in datos]),
                'total_pedidos_con_descuento': sum([d['total_pedidos'] for d in datos]),
                'promedio_descuento_general': round(
                    sum([d['porcentaje_descuento_promedio'] for d in datos]) / len(datos), 2
                ) if datos else 0
            }
        }
    
    def _generar_reporte_cumplimiento_metas(self, parametros):
        """Generar reporte de cumplimiento de metas del tabulador"""
        fecha_desde = parametros.get('fecha_desde', timezone.now().date().replace(day=1))
        fecha_hasta = parametros.get('fecha_hasta', timezone.now().date())
        
        # Obtener tabulador de descuentos
        tabulador = TabuladorDescuento.objects.all().order_by('rango_min')
        
        # Analizar pedidos del período
        pedidos = Pedido.objects.filter(
            fecha__date__range=[fecha_desde, fecha_hasta]
        ).values('cliente_id', 'cliente__nombre').annotate(
            total_compras=Sum('total'),
            total_pedidos=Count('id'),
            descuento_obtenido=Sum('descuento_aplicado')
        )
        
        datos = []
        for pedido_data in pedidos:
            total_compras = float(pedido_data['total_compras'])
            
            # Determinar descuento según tabulador
            descuento_esperado = 0
            nivel_tabulador = "Sin descuento"
            
            for tab in tabulador:
                if total_compras >= tab.rango_min and (tab.rango_max is None or total_compras <= tab.rango_max):
                    descuento_esperado = tab.porcentaje
                    nivel_tabulador = f"{tab.rango_min}-{tab.rango_max or '∞'}"
                    break
            
            descuento_obtenido = float(pedido_data['descuento_obtenido'] or 0)
            descuento_esperado_monto = (total_compras * float(descuento_esperado) / 100)
            
            cumplimiento = (descuento_obtenido / descuento_esperado_monto * 100) if descuento_esperado_monto > 0 else 0
            
            datos.append({
                'cliente_id': pedido_data['cliente_id'],
                'cliente_nombre': pedido_data['cliente__nombre'],
                'total_compras': total_compras,
                'total_pedidos': pedido_data['total_pedidos'],
                'nivel_tabulador': nivel_tabulador,
                'descuento_esperado_porcentaje': float(descuento_esperado),
                'descuento_esperado_monto': round(descuento_esperado_monto, 2),
                'descuento_obtenido': round(descuento_obtenido, 2),
                'cumplimiento_porcentaje': round(cumplimiento, 2),
                'diferencia': round(descuento_obtenido - descuento_esperado_monto, 2)
            })
        
        return {
            'titulo': 'Cumplimiento de Metas del Tabulador',
            'periodo': f"{fecha_desde} a {fecha_hasta}",
            'datos': sorted(datos, key=lambda x: x['total_compras'], reverse=True),
            'resumen': {
                'total_clientes_analizados': len(datos),
                'cumplimiento_promedio': round(
                    sum([d['cumplimiento_porcentaje'] for d in datos]) / len(datos), 2
                ) if datos else 0,
                'clientes_cumplimiento_100': len([d for d in datos if d['cumplimiento_porcentaje'] >= 100])
            }
        }
    
    def _generar_reporte_ventas_vendedor(self, parametros):
        """Generar reporte de ventas por vendedor"""
        fecha_desde = parametros.get('fecha_desde', timezone.now().date().replace(day=1))
        fecha_hasta = parametros.get('fecha_hasta', timezone.now().date())
        vendedor_id = parametros.get('vendedor_id')
        
        query = Pedido.objects.filter(
            fecha__date__range=[fecha_desde, fecha_hasta]
        ).select_related('created_by')
        
        if vendedor_id:
            query = query.filter(created_by_id=vendedor_id)
        
        # Agrupar por vendedor
        ventas_vendedor = query.values(
            'created_by_id', 
            'created_by__username', 
            'created_by__first_name', 
            'created_by__last_name'
        ).annotate(
            total_ventas=Sum('total'),
            total_pedidos=Count('id'),
            promedio_venta=Avg('total'),
            descuentos_aplicados=Sum('descuento_aplicado')
        )
        
        datos = []
        for venta in ventas_vendedor:
            datos.append({
                'vendedor_id': venta['created_by_id'],
                'vendedor_username': venta['created_by__username'],
                'vendedor_nombre': f"{venta['created_by__first_name'] or ''} {venta['created_by__last_name'] or ''}".strip(),
                'total_ventas': float(venta['total_ventas'] or 0),
                'total_pedidos': venta['total_pedidos'],
                'promedio_venta': round(float(venta['promedio_venta'] or 0), 2),
                'descuentos_aplicados': float(venta['descuentos_aplicados'] or 0)
            })
        
        return {
            'titulo': 'Ventas por Vendedor',
            'periodo': f"{fecha_desde} a {fecha_hasta}",
            'datos': sorted(datos, key=lambda x: x['total_ventas'], reverse=True),
            'resumen': {
                'total_vendedores': len(datos),
                'ventas_totales': sum([d['total_ventas'] for d in datos]),
                'promedio_ventas_vendedor': round(
                    sum([d['total_ventas'] for d in datos]) / len(datos), 2
                ) if datos else 0
            }
        }
    
    def _generar_reporte_productos_vendidos(self, parametros):
        """Generar reporte de productos más vendidos"""
        fecha_desde = parametros.get('fecha_desde', timezone.now().date().replace(day=1))
        fecha_hasta = parametros.get('fecha_hasta', timezone.now().date())
        limite = parametros.get('limite_registros', 50)
        
        # Agrupar por producto
        productos_vendidos = DetallePedido.objects.filter(
            pedido__fecha__date__range=[fecha_desde, fecha_hasta]
        ).select_related('producto').values(
            'producto_id',
            'producto__codigo',
            'producto__modelo',
            'producto__color'
        ).annotate(
            cantidad_vendida=Sum('cantidad'),
            total_ventas=Sum(F('cantidad') * F('precio_unitario')),
            total_pedidos=Count('pedido_id', distinct=True)
        ).order_by('-cantidad_vendida')[:limite]
        
        datos = []
        for producto in productos_vendidos:
            datos.append({
                'producto_id': producto['producto_id'],
                'producto_codigo': producto['producto__codigo'],
                'producto_descripcion': f"{producto['producto__modelo']} - {producto['producto__color']}",
                'cantidad_vendida': producto['cantidad_vendida'],
                'total_ventas': float(producto['total_ventas']),
                'total_pedidos': producto['total_pedidos'],
                'precio_promedio': round(float(producto['total_ventas']) / producto['cantidad_vendida'], 2)
            })
        
        return {
            'titulo': 'Productos Más Vendidos',
            'periodo': f"{fecha_desde} a {fecha_hasta}",
            'datos': datos,
            'resumen': {
                'total_productos_analizados': len(datos),
                'cantidad_total_vendida': sum([d['cantidad_vendida'] for d in datos]),
                'ventas_totales': sum([d['total_ventas'] for d in datos])
            }
        }
    
    def _generar_reporte_rentabilidad(self, parametros):
        """Generar reporte de análisis de rentabilidad"""
        fecha_desde = parametros.get('fecha_desde', timezone.now().date().replace(day=1))
        fecha_hasta = parametros.get('fecha_hasta', timezone.now().date())
        
        # Analizar por producto
        rentabilidad_productos = DetallePedido.objects.filter(
            pedido__fecha__date__range=[fecha_desde, fecha_hasta]
        ).select_related('producto').values(
            'producto_id',
            'producto__codigo',
            'producto__modelo',
            'producto__costo'
        ).annotate(
            cantidad_vendida=Sum('cantidad'),
            ingresos=Sum(F('cantidad') * F('precio_unitario')),
            costos=Sum(F('cantidad') * F('producto__costo'))
        )
        
        datos = []
        for producto in rentabilidad_productos:
            ingresos = float(producto['ingresos'])
            costos = float(producto['costos'] or 0)
            ganancia = ingresos - costos
            margen = (ganancia / ingresos * 100) if ingresos > 0 else 0
            
            datos.append({
                'producto_id': producto['producto_id'],
                'producto_codigo': producto['producto__codigo'],
                'producto_modelo': producto['producto__modelo'],
                'cantidad_vendida': producto['cantidad_vendida'],
                'ingresos': ingresos,
                'costos': costos,
                'ganancia': round(ganancia, 2),
                'margen_porcentaje': round(margen, 2)
            })
        
        return {
            'titulo': 'Análisis de Rentabilidad',
            'periodo': f"{fecha_desde} a {fecha_hasta}",
            'datos': sorted(datos, key=lambda x: x['ganancia'], reverse=True),
            'resumen': {
                'total_ingresos': sum([d['ingresos'] for d in datos]),
                'total_costos': sum([d['costos'] for d in datos]),
                'ganancia_total': sum([d['ganancia'] for d in datos]),
                'margen_promedio': round(
                    sum([d['margen_porcentaje'] for d in datos]) / len(datos), 2
                ) if datos else 0
            }
        }
    
    def _generar_reporte_stock_critico(self, parametros):
        """Generar reporte de stock crítico"""
        tienda_id = parametros.get('tienda_id')
        
        query = Inventario.objects.select_related('tienda', 'producto').filter(
            cantidad_actual__lte=5  # Stock crítico bajo
        )
        
        if tienda_id:
            query = query.filter(tienda_id=tienda_id)
        
        inventarios_criticos = query.all()
        
        datos = []
        for inv in inventarios_criticos:
            datos.append({
                'tienda_id': inv.tienda.id,
                'tienda_nombre': inv.tienda.nombre,
                'producto_id': inv.producto.id,
                'producto_codigo': inv.producto.codigo,
                'producto_descripcion': str(inv.producto),
                'cantidad_actual': inv.cantidad_actual,
                'cantidad_minima': 5,
                'diferencia': inv.cantidad_actual - 5,
                'nivel_criticidad': 'crítico' if inv.cantidad_actual == 0 else 'bajo'
            })
        
        return {
            'titulo': 'Stock Crítico y Alertas',
            'datos': sorted(datos, key=lambda x: x['diferencia']),
            'resumen': {
                'total_productos_criticos': len(datos),
                'productos_sin_stock': len([d for d in datos if d['cantidad_actual'] == 0]),
                'tiendas_afectadas': len(set([d['tienda_id'] for d in datos]))
            }
        }
    
    def _generar_reporte_tendencias_ventas(self, parametros):
        """Generar reporte de tendencias de ventas"""
        fecha_desde = parametros.get('fecha_desde', timezone.now().date() - timedelta(days=90))
        fecha_hasta = parametros.get('fecha_hasta', timezone.now().date())
        
        # Agrupar ventas por semana
        ventas_semanales = Pedido.objects.filter(
            fecha__date__range=[fecha_desde, fecha_hasta]
        ).extra(
            select={'semana': "strftime('%%Y-%%W', fecha)"}
        ).values('semana').annotate(
            total_ventas=Sum('total'),
            total_pedidos=Count('id'),
            promedio_pedido=Avg('total')
        ).order_by('semana')
        
        datos = []
        for semana in ventas_semanales:
            datos.append({
                'periodo': semana['semana'],
                'total_ventas': float(semana['total_ventas']),
                'total_pedidos': semana['total_pedidos'],
                'promedio_pedido': round(float(semana['promedio_pedido']), 2)
            })
        
        # Calcular tendencia
        if len(datos) >= 2:
            tendencia = "creciente" if datos[-1]['total_ventas'] > datos[0]['total_ventas'] else "decreciente"
        else:
            tendencia = "sin datos suficientes"
        
        return {
            'titulo': 'Tendencias de Ventas',
            'periodo': f"{fecha_desde} a {fecha_hasta}",
            'datos': datos,
            'resumen': {
                'total_semanas_analizadas': len(datos),
                'tendencia_general': tendencia,
                'mejor_semana': max(datos, key=lambda x: x['total_ventas'])['periodo'] if datos else None,
                'promedio_semanal': round(
                    sum([d['total_ventas'] for d in datos]) / len(datos), 2
                ) if datos else 0
            }
        }
    
    def _registrar_ejecucion(self, reporte_id, parametros, tiempo_ejecucion, registros_encontrados):
        """Registrar la ejecución del reporte"""
        try:
            reporte = ReportePersonalizado.objects.get(id=reporte_id)
            EjecucionReporte.objects.create(
                reporte=reporte,
                ejecutado_por=self.request.user,
                parametros_utilizados=parametros,
                tiempo_ejecucion=tiempo_ejecucion,
                registros_encontrados=registros_encontrados
            )
            
            # Actualizar última ejecución
            reporte.ultima_ejecucion = timezone.now()
            reporte.save()
        except ReportePersonalizado.DoesNotExist:
            pass
    
    def _generar_csv_response(self, resultado, tipo_reporte):
        """Generar respuesta CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{tipo_reporte}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        if 'datos' in resultado and resultado['datos']:
            # Escribir headers
            headers = list(resultado['datos'][0].keys())
            writer.writerow(headers)
            
            # Escribir datos
            for fila in resultado['datos']:
                writer.writerow([fila.get(header, '') for header in headers])
        
        return response
    
    def _generar_excel_response(self, resultado, tipo_reporte):
        """Generar respuesta Excel (simplificado como CSV por ahora)"""
        # Para implementación completa de Excel, se necesitaría openpyxl
        return self._generar_csv_response(resultado, tipo_reporte)


# Frontend Views
@login_required
def dashboard_reportes(request):
    """Dashboard principal de reportes"""
    reportes_disponibles = ReportePersonalizado.TIPO_CHOICES
    reportes_recientes = EjecucionReporte.objects.select_related(
        'reporte', 'ejecutado_por'
    ).order_by('-fecha_ejecucion')[:10]
    
    context = {
        'reportes_disponibles': reportes_disponibles,
        'reportes_recientes': reportes_recientes,
        'total_reportes': ReportePersonalizado.objects.count(),
        'total_ejecuciones': EjecucionReporte.objects.count()
    }
    
    return render(request, 'reportes/dashboard.html', context)

@login_required
def ejecutar_reporte(request, tipo_reporte):
    """Vista para ejecutar un reporte específico"""
    if request.method == 'POST':
        # Procesar parámetros y ejecutar reporte
        pass
    
    context = {
        'tipo_reporte': tipo_reporte,
        'tipo_display': dict(ReportePersonalizado.TIPO_CHOICES).get(tipo_reporte, tipo_reporte)
    }
    
    return render(request, 'reportes/ejecutar.html', context)
