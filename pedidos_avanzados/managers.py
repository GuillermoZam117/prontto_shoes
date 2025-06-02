"""
Managers personalizados para la gestión avanzada de pedidos
"""

from django.db import models
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.db.models import Q, Sum, Count


class OrdenClienteManager(models.Manager):
    """Manager personalizado para OrdenCliente con lógica de negocio"""
    
    def activas(self):
        """Obtiene órdenes activas (no cerradas ni canceladas)"""
        return self.filter(estado__in=['ACTIVO', 'PENDIENTE'])
    
    def vencidas(self):
        """Obtiene órdenes que han vencido"""
        fecha_limite = timezone.now() - timedelta(days=30)
        return self.filter(
            estado='ACTIVO',
            fecha_creacion__lt=fecha_limite
        )
    
    def con_credito_disponible(self):
        """Obtiene órdenes con crédito disponible"""
        return self.filter(
            estado='CERRADO',
            monto_pendiente__gt=0
        )
    
    def crear_orden_automatica(self, cliente, productos_data):
        """
        Crea una nueva orden cliente con productos automáticamente
        
        Args:
            cliente: Instancia del cliente
            productos_data: Lista de diccionarios con producto, cantidad, precio
            
        Returns:
            OrdenCliente: Orden creada
        """
        # Crear número de orden único
        ultimo_numero = self.filter(
            fecha_creacion__year=timezone.now().year
        ).count()
        numero_orden = f"ORD-{timezone.now().year}-{ultimo_numero + 1:06d}"
        
        # Calcular totales
        total_productos = sum(item['cantidad'] for item in productos_data)
        monto_total = sum(
            Decimal(str(item['cantidad'])) * Decimal(str(item['precio']))
            for item in productos_data
        )
        
        # Crear orden
        orden = self.create(
            numero_orden=numero_orden,
            cliente=cliente,
            estado='ACTIVO',
            total_productos=total_productos,
            monto_total=monto_total
        )
        
        return orden
    
    def consolidar_ordenes_cliente(self, cliente, ordenes_ids):
        """
        Consolida múltiples órdenes de un cliente en una sola
        
        Args:
            cliente: Cliente propietario de las órdenes
            ordenes_ids: Lista de IDs de órdenes a consolidar
            
        Returns:
            OrdenCliente: Orden consolidada
        """
        ordenes = self.filter(
            id__in=ordenes_ids,
            cliente=cliente,
            estado='ACTIVO'
        )
        
        if not ordenes.exists():
            raise ValueError("No hay órdenes válidas para consolidar")
        
        # Crear orden consolidada
        orden_principal = ordenes.first()
        total_productos = ordenes.aggregate(Sum('total_productos'))['total_productos__sum']
        monto_total = ordenes.aggregate(Sum('monto_total'))['monto_total__sum']
        
        orden_consolidada = self.create(
            numero_orden=f"CONS-{timezone.now().strftime('%Y%m%d')}-{cliente.id}",
            cliente=cliente,
            estado='ACTIVO',
            total_productos=total_productos,
            monto_total=monto_total,
            observaciones=f"Orden consolidada de {ordenes.count()} órdenes"
        )
        
        # Marcar órdenes originales como consolidadas
        ordenes.update(estado='CONSOLIDADO')
        
        return orden_consolidada


class EstadoProductoSeguimientoManager(models.Manager):
    """Manager para seguimiento de estados de productos"""
    
    def por_estado(self, estado):
        """Filtra productos por estado específico"""
        return self.filter(estado=estado)
    
    def pendientes_entrega(self):
        """Productos pendientes de entrega"""
        return self.filter(estado__in=['PEDIDO', 'PRODUCCION', 'LISTO'])
    
    def actualizar_estado_masivo(self, productos_ids, nuevo_estado, observaciones=None):
        """
        Actualiza el estado de múltiples productos
        
        Args:
            productos_ids: Lista de IDs de seguimiento
            nuevo_estado: Nuevo estado a aplicar
            observaciones: Observaciones opcionales
        """
        return self.filter(id__in=productos_ids).update(
            estado=nuevo_estado,
            fecha_cambio=timezone.now(),
            observaciones=observaciones or ''
        )
    
    def productos_atrasados(self):
        """Productos que han superado su fecha estimada de entrega"""
        return self.filter(
            fecha_entrega_estimada__lt=timezone.now().date(),
            estado__in=['PEDIDO', 'PRODUCCION', 'LISTO']
        )


class NotaCreditoManager(models.Manager):
    """Manager para manejo de notas de crédito"""
    
    def vigentes(self):
        """Notas de crédito vigentes (no vencidas ni aplicadas)"""
        return self.filter(
            aplicada=False,
            fecha_expiracion__gt=timezone.now()
        )
    
    def vencidas(self):
        """Notas de crédito vencidas"""
        return self.filter(
            aplicada=False,
            fecha_expiracion__lte=timezone.now()
        )
    
    def por_cliente(self, cliente):
        """Notas de crédito de un cliente específico"""
        return self.filter(cliente=cliente)
    
    def credito_disponible_cliente(self, cliente):
        """Calcula el crédito total disponible de un cliente"""
        credito_total = self.vigentes().filter(
            cliente=cliente,
            tipo='CREDITO'
        ).aggregate(Sum('monto'))['monto__sum'] or Decimal('0.00')
        
        debito_total = self.vigentes().filter(
            cliente=cliente,
            tipo='DEBITO'
        ).aggregate(Sum('monto'))['monto__sum'] or Decimal('0.00')
        
        return credito_total - debito_total
    
    def crear_nota_automatica(self, cliente, monto, tipo, origen_orden=None, motivo=''):
        """
        Crea una nota de crédito/débito automáticamente
        
        Args:
            cliente: Cliente propietario
            monto: Monto de la nota
            tipo: 'CREDITO' o 'DEBITO'
            origen_orden: Orden que origina la nota (opcional)
            motivo: Motivo de la nota
            
        Returns:
            NotaCredito: Nota creada
        """
        numero_nota = f"NC-{timezone.now().strftime('%Y%m%d')}-{self.count() + 1:06d}"
        
        return self.create(
            numero_nota=numero_nota,
            cliente=cliente,
            tipo=tipo,
            monto=monto,
            origen_orden=origen_orden,
            motivo=motivo,
            fecha_expiracion=timezone.now() + timedelta(days=60)
        )
    
    def aplicar_credito_a_orden(self, cliente, monto_aplicar, orden_destino):
        """
        Aplica crédito disponible a una orden específica
        
        Args:
            cliente: Cliente propietario del crédito
            monto_aplicar: Monto a aplicar
            orden_destino: Orden donde aplicar el crédito
            
        Returns:
            tuple: (monto_aplicado, notas_utilizadas)
        """
        notas_disponibles = self.vigentes().filter(
            cliente=cliente,
            tipo='CREDITO'
        ).order_by('fecha_expiracion')
        
        monto_pendiente = monto_aplicar
        notas_utilizadas = []
        
        for nota in notas_disponibles:
            if monto_pendiente <= 0:
                break
                
            if nota.monto <= monto_pendiente:
                # Aplicar toda la nota
                monto_aplicado_nota = nota.monto
                nota.aplicada = True
                nota.fecha_aplicacion = timezone.now()
                nota.orden_aplicacion = orden_destino
                nota.save()
            else:
                # Aplicar parcialmente - crear nueva nota con el resto
                monto_aplicado_nota = monto_pendiente
                nota_resto = self.create(
                    numero_nota=f"{nota.numero_nota}-RESTO",
                    cliente=cliente,
                    tipo='CREDITO',
                    monto=nota.monto - monto_aplicado_nota,
                    fecha_expiracion=nota.fecha_expiracion,
                    motivo=f"Resto de {nota.numero_nota}"
                )
                
                nota.monto = monto_aplicado_nota
                nota.aplicada = True
                nota.fecha_aplicacion = timezone.now()
                nota.orden_aplicacion = orden_destino
                nota.save()
            
            monto_pendiente -= monto_aplicado_nota
            notas_utilizadas.append(nota)
        
        monto_aplicado_total = monto_aplicar - monto_pendiente
        return monto_aplicado_total, notas_utilizadas


class EntregaParcialManager(models.Manager):
    """Manager para entregas parciales"""
    
    def por_orden(self, orden_cliente):
        """Entregas de una orden específica"""
        return self.filter(orden_cliente=orden_cliente)
    
    def pendientes_confirmacion(self):
        """Entregas pendientes de confirmación por cliente"""
        return self.filter(confirmado_por_cliente=False)
    
    def crear_entrega_parcial(self, orden_cliente, productos_entregados, observaciones=''):
        """
        Crea una nueva entrega parcial
        
        Args:
            orden_cliente: Orden cliente asociada
            productos_entregados: Lista de productos entregados
            observaciones: Observaciones adicionales
            
        Returns:
            EntregaParcial: Entrega creada
        """
        # Generar número de ticket único
        numero_ticket = f"EP-{orden_cliente.numero_orden}-{self.filter(orden_cliente=orden_cliente).count() + 1:03d}"
        
        # Calcular totales
        total_productos = sum(item['cantidad'] for item in productos_entregados)
        monto_parcial = sum(
            Decimal(str(item['cantidad'])) * Decimal(str(item['precio']))
            for item in productos_entregados
        )
        
        return self.create(
            numero_ticket=numero_ticket,
            orden_cliente=orden_cliente,
            total_productos_entregados=total_productos,
            monto_parcial=monto_parcial,
            observaciones=observaciones
        )
