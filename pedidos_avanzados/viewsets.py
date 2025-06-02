"""
ViewSets para el sistema de pedidos avanzados
Sistema POS Pronto Shoes
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import (
    OrdenCliente, EstadoProductoSeguimiento, EntregaParcial,
    NotaCredito, PortalClientePolitica, ProductoCompartir
)
from .serializers import (
    OrdenClienteSerializer, OrdenClienteListSerializer,
    EstadoProductoSeguimientoSerializer, EntregaParcialSerializer,
    NotaCreditoSerializer, PortalClientePoliticaSerializer,
    ProductoCompartirSerializer, CrearOrdenDesdepedidosSerializer,
    ProcesarEntregaParcialSerializer, AplicarCreditoSerializer,
    RegistrarCompartidoSerializer
)
from .services import (
    ServicioPedidosAvanzados, ServicioAutomatizacionClientes,
    ServicioCompartirProductos
)
from ventas.models import Pedido
from clientes.models import Cliente
from productos.models import Producto


class OrdenClienteViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de órdenes de cliente"""
    
    queryset = OrdenCliente.objects.all().select_related('cliente')
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'list':
            return OrdenClienteListSerializer
        return OrdenClienteSerializer
    
    def get_queryset(self):
        """Filtra queryset según parámetros"""
        queryset = super().get_queryset()
        
        # Filtros por parámetros de query
        estado = self.request.query_params.get('estado')
        cliente_id = self.request.query_params.get('cliente_id')
        fecha_desde = self.request.query_params.get('fecha_desde')
        fecha_hasta = self.request.query_params.get('fecha_hasta')
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        if fecha_desde:
            queryset = queryset.filter(fecha_creacion__gte=fecha_desde)
        
        if fecha_hasta:
            queryset = queryset.filter(fecha_creacion__lte=fecha_hasta)
        
        return queryset.order_by('-fecha_creacion')
    
    def perform_create(self, serializer):
        """Establece usuario creador al crear orden"""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Establece usuario actualizador al actualizar orden"""
        serializer.save(updated_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def crear_desde_pedidos(self, request):
        """
        Crea una orden cliente consolidando múltiples pedidos
        
        POST /api/ordenes-cliente/crear_desde_pedidos/
        {
            "cliente_id": 1,
            "pedidos_ids": [1, 2, 3],
            "observaciones": "Consolidación automática"
        }
        """
        serializer = CrearOrdenDesdepedidosSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                cliente = Cliente.objects.get(id=serializer.validated_data['cliente_id'])
                pedidos_ids = serializer.validated_data['pedidos_ids']
                
                orden_cliente = ServicioPedidosAvanzados.crear_orden_cliente_desde_pedidos(
                    cliente=cliente,
                    pedidos_ids=pedidos_ids
                )
                
                # Agregar observaciones si se proporcionaron
                observaciones = serializer.validated_data.get('observaciones')
                if observaciones:
                    orden_cliente.observaciones = observaciones
                    orden_cliente.save()
                
                response_serializer = OrdenClienteSerializer(orden_cliente)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
                
            except ValueError as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {'error': f'Error interno: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def convertir_a_venta(self, request, pk=None):
        """
        Convierte una orden cliente completa a ventas
        
        POST /api/ordenes-cliente/{id}/convertir_a_venta/
        """
        orden_cliente = self.get_object()
        
        try:
            pedidos_convertidos = ServicioPedidosAvanzados.convertir_orden_a_venta(orden_cliente)
            
            return Response({
                'message': f'Orden convertida a venta exitosamente',
                'pedidos_convertidos': [p.id for p in pedidos_convertidos],
                'orden_id': orden_cliente.id
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Obtiene estadísticas de órdenes cliente
        
        GET /api/ordenes-cliente/estadisticas/
        """
        stats = ServicioAutomatizacionClientes.generar_reporte_ordenes_pendientes()
        return Response(stats, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def activas(self, request):
        """
        Obtiene solo órdenes activas
        
        GET /api/ordenes-cliente/activas/
        """
        queryset = self.get_queryset().filter(estado='ACTIVO')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """
        Obtiene solo órdenes pendientes
        
        GET /api/ordenes-cliente/pendientes/
        """
        queryset = self.get_queryset().filter(estado='PENDIENTE')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class EstadoProductoSeguimientoViewSet(viewsets.ModelViewSet):
    """ViewSet para seguimiento de estados de productos"""
    
    queryset = EstadoProductoSeguimiento.objects.all().select_related(
        'detalle_pedido__producto', 'detalle_pedido__pedido', 'usuario_cambio', 'proveedor'
    )
    serializer_class = EstadoProductoSeguimientoSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtra queryset según parámetros"""
        queryset = super().get_queryset()
        
        estado = self.request.query_params.get('estado')
        pedido_id = self.request.query_params.get('pedido_id')
        producto_id = self.request.query_params.get('producto_id')
        
        if estado:
            queryset = queryset.filter(estado_nuevo=estado)
        
        if pedido_id:
            queryset = queryset.filter(detalle_pedido__pedido_id=pedido_id)
        
        if producto_id:
            queryset = queryset.filter(detalle_pedido__producto_id=producto_id)
        
        return queryset.order_by('-fecha_cambio')
    
    def perform_create(self, serializer):
        """Establece usuario que hace el cambio"""
        serializer.save(usuario_cambio=self.request.user)
    
    @action(detail=False, methods=['get'])
    def por_estado(self, request):
        """
        Obtiene productos agrupados por estado
        
        GET /api/seguimiento-productos/por_estado/
        """
        from django.db.models import Count
        
        estados = EstadoProductoSeguimiento.objects.values('estado_nuevo').annotate(
            count=Count('id')
        ).order_by('estado_nuevo')
        
        return Response(list(estados))
    
    @action(detail=False, methods=['get'])
    def atrasados(self, request):
        """
        Obtiene productos atrasados (sin fecha estimada vencida)
        
        GET /api/seguimiento-productos/atrasados/
        """
        # Por simplicidad, consideramos atrasados los que están en ciertos estados por más de 7 días
        fecha_limite = timezone.now() - timedelta(days=7)
        
        queryset = self.get_queryset().filter(
            estado_nuevo__in=['PEDIDO', 'SOLICITADO_PROVEEDOR', 'EN_ESPERA'],
            fecha_cambio__lt=fecha_limite
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def actualizar_estado_masivo(self, request):
        """
        Actualiza el estado de múltiples productos
        
        POST /api/seguimiento-productos/actualizar_estado_masivo/
        {
            "seguimientos_ids": [1, 2, 3],
            "nuevo_estado": "LISTO_ENTREGA",
            "observaciones": "Productos listos para entrega"
        }
        """
        seguimientos_ids = request.data.get('seguimientos_ids', [])
        nuevo_estado = request.data.get('nuevo_estado')
        observaciones = request.data.get('observaciones', '')
        
        if not seguimientos_ids or not nuevo_estado:
            return Response(
                {'error': 'Se requieren seguimientos_ids y nuevo_estado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar estado
        estados_validos = [choice[0] for choice in EstadoProductoSeguimiento.ESTADOS_PRODUCTO]
        if nuevo_estado not in estados_validos:
            return Response(
                {'error': f'Estado inválido. Estados válidos: {estados_validos}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear nuevos seguimientos para cada producto
        seguimientos_actualizados = []
        for seguimiento_id in seguimientos_ids:
            try:
                seguimiento_actual = EstadoProductoSeguimiento.objects.get(id=seguimiento_id)
                
                nuevo_seguimiento = EstadoProductoSeguimiento.objects.create(
                    detalle_pedido=seguimiento_actual.detalle_pedido,
                    estado_anterior=seguimiento_actual.estado_nuevo,
                    estado_nuevo=nuevo_estado,
                    usuario_cambio=request.user,
                    observaciones=observaciones
                )
                seguimientos_actualizados.append(nuevo_seguimiento)
                
            except EstadoProductoSeguimiento.DoesNotExist:
                continue
        
        serializer = self.get_serializer(seguimientos_actualizados, many=True)
        return Response({
            'message': f'{len(seguimientos_actualizados)} productos actualizados',
            'seguimientos': serializer.data
        }, status=status.HTTP_200_OK)


class EntregaParcialViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de entregas parciales"""
    
    queryset = EntregaParcial.objects.all().select_related(
        'pedido_original', 'pedido_nuevo', 'usuario_entrega'
    )
    serializer_class = EntregaParcialSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtra queryset según parámetros"""
        queryset = super().get_queryset()
        
        pedido_id = self.request.query_params.get('pedido_id')
        fecha_desde = self.request.query_params.get('fecha_desde')
        fecha_hasta = self.request.query_params.get('fecha_hasta')
        
        if pedido_id:
            queryset = queryset.filter(
                Q(pedido_original_id=pedido_id) | Q(pedido_nuevo_id=pedido_id)
            )
        
        if fecha_desde:
            queryset = queryset.filter(fecha_entrega__gte=fecha_desde)
        
        if fecha_hasta:
            queryset = queryset.filter(fecha_entrega__lte=fecha_hasta)
        
        return queryset.order_by('-fecha_entrega')
    
    def perform_create(self, serializer):
        """Establece usuario que realiza la entrega"""
        serializer.save(usuario_entrega=self.request.user)
    
    @action(detail=False, methods=['post'])
    def procesar_entrega(self, request):
        """
        Procesa una entrega parcial completa
        
        POST /api/entregas-parciales/procesar_entrega/
        {
            "pedido_id": 1,
            "productos_entregar": [
                {"detalle_id": 1, "cantidad_entregar": 2},
                {"detalle_id": 2, "cantidad_entregar": 1}
            ],
            "observaciones": "Entrega parcial",
            "metodo_pago": "efectivo"
        }
        """
        serializer = ProcesarEntregaParcialSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                pedido = Pedido.objects.get(id=serializer.validated_data['pedido_id'])
                productos_entregar = serializer.validated_data['productos_entregar']
                
                entrega_parcial, pedido_nuevo = ServicioPedidosAvanzados.procesar_entrega_parcial(
                    pedido_original=pedido,
                    productos_entregar=productos_entregar,
                    usuario_entrega=request.user
                )
                
                # Agregar información adicional
                observaciones = serializer.validated_data.get('observaciones')
                metodo_pago = serializer.validated_data.get('metodo_pago')
                
                if observaciones:
                    entrega_parcial.observaciones = observaciones
                if metodo_pago:
                    entrega_parcial.metodo_pago = metodo_pago
                
                entrega_parcial.save()
                
                response_serializer = EntregaParcialSerializer(entrega_parcial)
                return Response({
                    'entrega_parcial': response_serializer.data,
                    'pedido_nuevo_id': pedido_nuevo.id,
                    'message': 'Entrega parcial procesada exitosamente'
                }, status=status.HTTP_201_CREATED)
                
            except ValueError as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {'error': f'Error interno: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotaCreditoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de notas de crédito"""
    
    queryset = NotaCredito.objects.all().select_related(
        'cliente', 'pedido_origen', 'aplicada_en_pedido', 'created_by'
    )
    serializer_class = NotaCreditoSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtra queryset según parámetros"""
        queryset = super().get_queryset()
        
        cliente_id = self.request.query_params.get('cliente_id')
        tipo = self.request.query_params.get('tipo')
        estado = self.request.query_params.get('estado')
        
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Establece usuario creador"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def vigentes(self, request):
        """
        Obtiene notas de crédito vigentes
        
        GET /api/notas-credito/vigentes/
        """
        queryset = self.get_queryset().filter(
            estado='ACTIVA',
            fecha_vencimiento__gt=timezone.now().date()
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def vencidas(self, request):
        """
        Obtiene notas de crédito vencidas
        
        GET /api/notas-credito/vencidas/
        """
        queryset = self.get_queryset().filter(
            estado='ACTIVA',
            fecha_vencimiento__lte=timezone.now().date()
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def aplicar_credito(self, request):
        """
        Aplica crédito disponible a un pedido
        
        POST /api/notas-credito/aplicar_credito/
        {
            "cliente_id": 1,
            "pedido_id": 1,
            "monto_aplicar": 100.00  // opcional
        }
        """
        serializer = AplicarCreditoSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                cliente = Cliente.objects.get(id=serializer.validated_data['cliente_id'])
                pedido = serializer.validated_data['pedido']
                monto_aplicar = serializer.validated_data.get('monto_aplicar')
                
                monto_aplicado, notas_utilizadas = ServicioPedidosAvanzados.aplicar_credito_a_pedido(
                    cliente=cliente,
                    pedido=pedido,
                    monto_aplicar=monto_aplicar
                )
                
                return Response({
                    'monto_aplicado': monto_aplicado,
                    'notas_utilizadas': [n.id for n in notas_utilizadas],
                    'nuevo_total_pedido': pedido.total,
                    'message': f'Crédito aplicado exitosamente: ${monto_aplicado}'
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response(
                    {'error': f'Error al aplicar crédito: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def credito_disponible(self, request):
        """
        Obtiene el crédito disponible de un cliente
        
        GET /api/notas-credito/credito_disponible/?cliente_id=1
        """
        cliente_id = request.query_params.get('cliente_id')
        
        if not cliente_id:
            return Response(
                {'error': 'Se requiere cliente_id'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cliente = Cliente.objects.get(id=cliente_id)
            
            credito_total = NotaCredito.objects.filter(
                cliente=cliente,
                tipo='CREDITO',
                estado='ACTIVA',
                fecha_vencimiento__gt=timezone.now().date()
            ).aggregate(Sum('monto'))['monto__sum'] or Decimal('0.00')
            
            debito_total = NotaCredito.objects.filter(
                cliente=cliente,
                tipo='DEBITO',
                estado='ACTIVA',
                fecha_vencimiento__gt=timezone.now().date()
            ).aggregate(Sum('monto'))['monto__sum'] or Decimal('0.00')
            
            credito_neto = credito_total - debito_total
            
            return Response({
                'cliente_id': cliente_id,
                'cliente_nombre': cliente.nombre,
                'credito_total': credito_total,
                'debito_total': debito_total,
                'credito_disponible': max(credito_neto, Decimal('0.00'))
            })
            
        except Cliente.DoesNotExist:
            return Response(
                {'error': 'Cliente no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class PortalClientePoliticaViewSet(viewsets.ModelViewSet):
    """ViewSet para políticas del portal de cliente"""
    
    queryset = PortalClientePolitica.objects.filter(activo=True)
    serializer_class = PortalClientePoliticaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtra queryset según parámetros"""
        queryset = super().get_queryset()
        
        tipo = self.request.query_params.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        return queryset.order_by('tipo', 'orden_display')
    
    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        """
        Obtiene políticas agrupadas por tipo
        
        GET /api/portal-politicas/por_tipo/
        """
        tipos = {}
        for politica in self.get_queryset():
            if politica.tipo not in tipos:
                tipos[politica.tipo] = []
            tipos[politica.tipo].append(self.get_serializer(politica).data)
        
        return Response(tipos)


class ProductoCompartirViewSet(viewsets.ModelViewSet):
    """ViewSet para productos compartidos"""
    
    queryset = ProductoCompartir.objects.all().select_related('producto', 'cliente')
    serializer_class = ProductoCompartirSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtra queryset según parámetros"""
        queryset = super().get_queryset()
        
        cliente_id = self.request.query_params.get('cliente_id')
        producto_id = self.request.query_params.get('producto_id')
        plataforma = self.request.query_params.get('plataforma')
        
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        if producto_id:
            queryset = queryset.filter(producto_id=producto_id)
        
        if plataforma:
            queryset = queryset.filter(plataforma=plataforma)
        
        return queryset.order_by('-fecha_compartido')
    
    @action(detail=False, methods=['post'])
    def registrar_compartido(self, request):
        """
        Registra un nuevo producto compartido
        
        POST /api/productos-compartir/registrar_compartido/
        {
            "producto_id": 1,
            "cliente_id": 1,
            "plataforma": "FACEBOOK",
            "url_compartida": "https://facebook.com/..."
        }
        """
        serializer = RegistrarCompartidoSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                producto = Producto.objects.get(id=serializer.validated_data['producto_id'])
                cliente = Cliente.objects.get(id=serializer.validated_data['cliente_id'])
                
                compartido = ServicioCompartirProductos.registrar_compartido(
                    producto=producto,
                    cliente=cliente,
                    plataforma=serializer.validated_data['plataforma'],
                    url_compartida=serializer.validated_data.get('url_compartida')
                )
                
                response_serializer = ProductoCompartirSerializer(compartido)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
                
            except (Producto.DoesNotExist, Cliente.DoesNotExist) as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def registrar_click(self, request, pk=None):
        """
        Registra un click en un enlace compartido
        
        POST /api/productos-compartir/{id}/registrar_click/
        """
        ServicioCompartirProductos.registrar_click_compartido(pk)
        return Response({'message': 'Click registrado'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Obtiene estadísticas de productos compartidos
        
        GET /api/productos-compartir/estadisticas/
        """
        fecha_desde = request.query_params.get('fecha_desde')
        fecha_hasta = request.query_params.get('fecha_hasta')
        
        stats = ServicioCompartirProductos.obtener_estadisticas_compartidos(
            fecha_inicio=timezone.datetime.fromisoformat(fecha_desde) if fecha_desde else None,
            fecha_fin=timezone.datetime.fromisoformat(fecha_hasta) if fecha_hasta else None
        )
        
        return Response(stats)
