"""
Servicios de lógica de negocio para el sistema de pedidos avanzados
Sistema POS Pronto Shoes
"""

from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from typing import List, Dict, Optional, Tuple

from .models import (
    OrdenCliente, EstadoProductoSeguimiento, EntregaParcial, 
    NotaCredito, ProductoCompartir
)
from ventas.models import Pedido, DetallePedido
from clientes.models import Cliente
from productos.models import Producto


class ServicioPedidosAvanzados:
    """Servicio principal para gestión de pedidos avanzados"""
    
    @staticmethod
    def crear_orden_cliente_desde_pedidos(cliente: Cliente, pedidos_ids: List[int]) -> OrdenCliente:
        """
        Crea una OrdenCliente consolidando múltiples pedidos existentes
        
        Args:
            cliente: Cliente propietario
            pedidos_ids: Lista de IDs de pedidos a consolidar
            
        Returns:
            OrdenCliente: Nueva orden cliente creada
        """
        with transaction.atomic():
            # Validar pedidos
            pedidos = Pedido.objects.filter(
                id__in=pedidos_ids,
                cliente=cliente,
                estado='pendiente'
            ).select_related('cliente')
            
            if not pedidos.exists():
                raise ValueError("No se encontraron pedidos válidos para consolidar")
            
            # Calcular totales
            total_productos = sum(
                pedido.detalles.count() for pedido in pedidos
            )
            monto_total = sum(pedido.total for pedido in pedidos)
            
            # Crear número de orden único
            numero_orden = f"ORD-{timezone.now().strftime('%Y%m%d%H%M%S')}-{cliente.id}"
            
            # Crear orden cliente
            orden_cliente = OrdenCliente.objects.create(
                cliente=cliente,
                numero_orden=numero_orden,
                estado='ACTIVO',
                total_productos=total_productos,
                monto_total=monto_total,
                observaciones=f"Consolidado de {pedidos.count()} pedidos"
            )
            
            # Actualizar pedidos para referenciar la orden cliente
            for pedido in pedidos:
                pedido.estado = 'activo'
                pedido.save()
                
                # Crear seguimiento inicial para cada producto
                for detalle in pedido.detalles.all():
                    EstadoProductoSeguimiento.objects.create(
                        detalle_pedido=detalle,
                        estado_nuevo='APARTADO',
                        observaciones=f"Consolidado en orden {numero_orden}"
                    )
            
            return orden_cliente
    
    @staticmethod
    def procesar_entrega_parcial(
        pedido_original: Pedido, 
        productos_entregar: List[Dict],
        usuario_entrega=None
    ) -> Tuple[EntregaParcial, Pedido]:
        """
        Procesa una entrega parcial dividiendo el pedido original
        
        Args:
            pedido_original: Pedido original a dividir
            productos_entregar: Lista de productos a entregar
                [{'detalle_id': int, 'cantidad_entregar': int}]
            usuario_entrega: Usuario que realiza la entrega
            
        Returns:
            Tuple[EntregaParcial, Pedido]: (Entrega creada, Nuevo pedido con productos restantes)
        """
        with transaction.atomic():
            if not pedido_original.permite_entrega_parcial:
                raise ValueError("Este pedido no permite entregas parciales")
            
            # Crear nuevo pedido para productos restantes
            pedido_nuevo = Pedido.objects.create(
                cliente=pedido_original.cliente,
                fecha=timezone.now(),
                estado='pendiente',
                total=Decimal('0.00'),
                tienda=pedido_original.tienda,
                tipo=pedido_original.tipo,
                descuento_aplicado=pedido_original.descuento_aplicado,
                es_pedido_padre=False,
                pedido_padre=pedido_original,
                permite_entrega_parcial=True
            )
            
            # Generar ticket único
            pedido_original.generar_numero_ticket()
            
            monto_entregado = Decimal('0.00')
            productos_entregados_info = []
            
            # Procesar cada producto a entregar
            for item in productos_entregar:
                detalle_original = DetallePedido.objects.get(
                    id=item['detalle_id'],
                    pedido=pedido_original
                )
                
                cantidad_entregar = item['cantidad_entregar']
                cantidad_restante = detalle_original.cantidad - cantidad_entregar
                
                if cantidad_entregar <= 0 or cantidad_entregar > detalle_original.cantidad:
                    raise ValueError(f"Cantidad inválida para producto {detalle_original.producto.codigo}")
                
                # Calcular montos
                precio_unit = detalle_original.precio_unitario
                monto_producto = precio_unit * cantidad_entregar
                monto_entregado += monto_producto
                
                # Actualizar detalle original
                detalle_original.cantidad = cantidad_entregar
                detalle_original.subtotal = monto_producto
                detalle_original.save()
                
                # Crear detalle en pedido nuevo si queda cantidad
                if cantidad_restante > 0:
                    DetallePedido.objects.create(
                        pedido=pedido_nuevo,
                        producto=detalle_original.producto,
                        cantidad=cantidad_restante,
                        precio_unitario=precio_unit,
                        subtotal=precio_unit * cantidad_restante
                    )
                
                # Actualizar seguimiento
                EstadoProductoSeguimiento.objects.create(
                    detalle_pedido=detalle_original,
                    estado_nuevo='LISTO_ENTREGA',
                    observaciones=f"Entrega parcial - Ticket: {pedido_original.numero_ticket}"
                )
                
                productos_entregados_info.append({
                    'producto_id': detalle_original.producto.id,
                    'codigo': detalle_original.producto.codigo,
                    'cantidad': cantidad_entregar,
                    'precio_unitario': float(precio_unit),
                    'subtotal': float(monto_producto)
                })
            
            # Actualizar totales
            pedido_original.total = monto_entregado
            pedido_original.estado = 'surtido'
            pedido_original.save()
            
            # Calcular total del pedido nuevo
            total_nuevo = sum(
                detalle.subtotal for detalle in pedido_nuevo.detalles.all()
            )
            pedido_nuevo.total = total_nuevo
            pedido_nuevo.save()
            
            # Crear registro de entrega parcial
            entrega_parcial = EntregaParcial.objects.create(
                pedido_original=pedido_original,
                pedido_nuevo=pedido_nuevo,
                ticket_entrega=pedido_original.numero_ticket,
                productos_entregados=productos_entregados_info,
                monto_entregado=monto_entregado,
                usuario_entrega=usuario_entrega,
                observaciones=f"Entrega parcial procesada automáticamente"
            )
            
            return entrega_parcial, pedido_nuevo
    
    @staticmethod
    def convertir_orden_a_venta(orden_cliente: OrdenCliente) -> List[Pedido]:
        """
        Convierte una orden cliente completa a ventas
        
        Args:
            orden_cliente: Orden a convertir
            
        Returns:
            List[Pedido]: Pedidos convertidos a venta
        """
        with transaction.atomic():
            if not orden_cliente.esta_completa:
                raise ValueError("La orden no está completa para convertir a venta")
            
            # Buscar todos los pedidos relacionados con esta orden
            # (Esta lógica se puede mejorar con una relación directa)
            pedidos_relacionados = Pedido.objects.filter(
                cliente=orden_cliente.cliente,
                fecha__gte=orden_cliente.fecha_creacion,
                estado__in=['surtido', 'activo']
            )
            
            pedidos_convertidos = []
            
            for pedido in pedidos_relacionados:
                pedido.convertir_a_venta()
                pedidos_convertidos.append(pedido)
            
            # Actualizar orden cliente
            orden_cliente.estado = 'VENTA'
            orden_cliente.fecha_cierre = timezone.now()
            orden_cliente.save()
            
            return pedidos_convertidos
    
    @staticmethod
    def crear_nota_credito_automatica(
        cliente: Cliente, 
        monto: Decimal, 
        tipo: str, 
        motivo: str,
        pedido_origen: Optional[Pedido] = None
    ) -> NotaCredito:
        """
        Crea una nota de crédito/débito automáticamente
        
        Args:
            cliente: Cliente propietario
            monto: Monto de la nota
            tipo: 'CREDITO' o 'DEBITO'
            motivo: Motivo de la nota
            pedido_origen: Pedido que origina la nota (opcional)
            
        Returns:
            NotaCredito: Nota creada
        """
        return NotaCredito.objects.create(
            cliente=cliente,
            tipo=tipo,
            monto=monto,
            motivo=motivo,
            pedido_origen=pedido_origen,
            fecha_vencimiento=timezone.now().date() + timedelta(days=60)
        )
    
    @staticmethod
    def aplicar_credito_a_pedido(
        cliente: Cliente,
        pedido: Pedido,
        monto_aplicar: Optional[Decimal] = None
    ) -> Tuple[Decimal, List[NotaCredito]]:
        """
        Aplica crédito disponible del cliente a un pedido
        
        Args:
            cliente: Cliente propietario del crédito
            pedido: Pedido donde aplicar el crédito
            monto_aplicar: Monto específico a aplicar (opcional)
            
        Returns:
            Tuple[Decimal, List[NotaCredito]]: (Monto aplicado, Notas utilizadas)
        """
        with transaction.atomic():
            # Obtener crédito disponible
            notas_credito = NotaCredito.objects.filter(
                cliente=cliente,
                tipo='CREDITO',
                estado='ACTIVA',
                fecha_vencimiento__gt=timezone.now().date()
            ).order_by('fecha_vencimiento')
            
            credito_disponible = sum(nota.monto for nota in notas_credito)
            
            if credito_disponible == 0:
                return Decimal('0.00'), []
            
            # Determinar monto a aplicar
            if monto_aplicar is None:
                monto_aplicar = min(credito_disponible, pedido.total)
            else:
                monto_aplicar = min(monto_aplicar, credito_disponible, pedido.total)
            
            # Aplicar crédito
            monto_pendiente = monto_aplicar
            notas_utilizadas = []
            
            for nota in notas_credito:
                if monto_pendiente <= 0:
                    break
                
                if nota.monto <= monto_pendiente:
                    # Usar toda la nota
                    monto_usado = nota.monto
                    nota.estado = 'APLICADA'
                    nota.aplicada_en_pedido = pedido
                    nota.fecha_aplicacion = timezone.now()
                    nota.save()
                else:
                    # Usar parcialmente la nota
                    monto_usado = monto_pendiente
                    
                    # Crear nueva nota con el resto
                    NotaCredito.objects.create(
                        cliente=cliente,
                        tipo='CREDITO',
                        monto=nota.monto - monto_usado,
                        motivo=f"Resto de aplicación parcial - Nota original: {nota.id}",
                        fecha_vencimiento=nota.fecha_vencimiento
                    )
                    
                    # Actualizar nota original
                    nota.monto = monto_usado
                    nota.estado = 'APLICADA'
                    nota.aplicada_en_pedido = pedido
                    nota.fecha_aplicacion = timezone.now()
                    nota.save()
                
                monto_pendiente -= monto_usado
                notas_utilizadas.append(nota)
            
            monto_aplicado = monto_aplicar - monto_pendiente
            
            # Actualizar total del pedido
            pedido.total -= monto_aplicado
            pedido.save()
            
            return monto_aplicado, notas_utilizadas


class ServicioAutomatizacionClientes:
    """Servicio para automatización de gestión de clientes"""
    
    @staticmethod
    def procesar_clientes_inactivos():
        """
        Procesa clientes inactivos (30 días sin pedidos)
        Mueve a estado inactivo automáticamente
        """
        fecha_limite = timezone.now() - timedelta(days=30)
        
        clientes_inactivos = Cliente.objects.filter(
            activo=True,
            created_at__lt=fecha_limite
        ).exclude(
            pedidos__fecha__gte=fecha_limite
        )
        
        count = clientes_inactivos.update(activo=False)
        return count
    
    @staticmethod
    def procesar_notas_credito_vencidas():
        """
        Procesa notas de crédito vencidas (60 días)
        Marca como vencidas automáticamente
        """
        fecha_hoy = timezone.now().date()
        
        notas_vencidas = NotaCredito.objects.filter(
            estado='ACTIVA',
            fecha_vencimiento__lt=fecha_hoy
        )
        
        count = notas_vencidas.update(estado='VENCIDA')
        return count
    
    @staticmethod
    def generar_reporte_ordenes_pendientes():
        """
        Genera reporte de órdenes pendientes y estadísticas
        
        Returns:
            Dict: Reporte con estadísticas
        """
        ordenes_activas = OrdenCliente.objects.filter(estado='ACTIVO')
        ordenes_pendientes = OrdenCliente.objects.filter(estado='PENDIENTE')
        
        return {
            'ordenes_activas': ordenes_activas.count(),
            'ordenes_pendientes': ordenes_pendientes.count(),
            'monto_total_activas': sum(orden.monto_total for orden in ordenes_activas),
            'monto_total_pendientes': sum(orden.monto_total for orden in ordenes_pendientes),
            'clientes_con_ordenes_activas': ordenes_activas.values_list('cliente', flat=True).distinct().count(),
            'promedio_productos_por_orden': (
                sum(orden.total_productos for orden in ordenes_activas) / ordenes_activas.count()
                if ordenes_activas.count() > 0 else 0
            )
        }


class ServicioCompartirProductos:
    """Servicio para gestión de compartir productos en redes sociales"""
    
    @staticmethod
    def registrar_compartido(
        producto: Producto,
        cliente: Cliente,
        plataforma: str,
        url_compartida: Optional[str] = None
    ) -> ProductoCompartir:
        """
        Registra cuando un cliente comparte un producto
        
        Args:
            producto: Producto compartido
            cliente: Cliente que comparte
            plataforma: Plataforma donde se compartió
            url_compartida: URL compartida (opcional)
            
        Returns:
            ProductoCompartir: Registro creado
        """
        return ProductoCompartir.objects.create(
            producto=producto,
            cliente=cliente,
            plataforma=plataforma,
            url_compartida=url_compartida
        )
    
    @staticmethod
    def registrar_click_compartido(compartido_id: int):
        """
        Registra un click en un enlace compartido
        
        Args:
            compartido_id: ID del registro de compartido
        """
        try:
            compartido = ProductoCompartir.objects.get(id=compartido_id)
            compartido.clicks_generados += 1
            compartido.save()
        except ProductoCompartir.DoesNotExist:
            pass  # Ignorar clicks inválidos
    
    @staticmethod
    def obtener_estadisticas_compartidos(
        fecha_inicio: Optional[timezone.datetime] = None,
        fecha_fin: Optional[timezone.datetime] = None
    ) -> Dict:
        """
        Obtiene estadísticas de productos compartidos
        
        Args:
            fecha_inicio: Fecha de inicio del rango (opcional)
            fecha_fin: Fecha de fin del rango (opcional)
            
        Returns:
            Dict: Estadísticas de compartidos
        """
        queryset = ProductoCompartir.objects.all()
        
        if fecha_inicio:
            queryset = queryset.filter(fecha_compartido__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(fecha_compartido__lte=fecha_fin)
        
        from django.db.models import Count, Sum
        
        stats = queryset.aggregate(
            total_compartidos=Count('id'),
            total_clicks=Sum('clicks_generados')
        )
        
        # Estadísticas por plataforma
        por_plataforma = queryset.values('plataforma').annotate(
            count=Count('id'),
            clicks=Sum('clicks_generados')
        ).order_by('-count')
        
        # Productos más compartidos
        productos_top = queryset.values(
            'producto__codigo', 'producto__nombre'
        ).annotate(
            compartidos=Count('id'),
            clicks=Sum('clicks_generados')
        ).order_by('-compartidos')[:10]
        
        return {
            'resumen': stats,
            'por_plataforma': list(por_plataforma),
            'productos_top': list(productos_top)
        }
