from django.db import models
from decimal import Decimal
from tiendas.models import Tienda
from django.contrib.auth import get_user_model
# from productos.models import Producto # Remove direct import
from requisiciones.models import DetalleRequisicion
from django.utils import timezone

class Proveedor(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    contacto = models.CharField(max_length=100, blank=True)
    requiere_anticipo = models.BooleanField(default=False)
    max_return_days = models.PositiveIntegerField(default=0)
    
    # Enhanced supplier tracking fields
    tiempo_entrega_promedio = models.PositiveIntegerField(default=7, help_text="Días promedio de entrega")
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)
    rating_calidad = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('5.0'), help_text="Rating de calidad 1-5")
    rating_puntualidad = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('5.0'), help_text="Rating de puntualidad 1-5")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(get_user_model(), related_name='proveedores_creados', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(get_user_model(), related_name='proveedores_actualizados', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nombre

class PurchaseOrder(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado por Proveedor'),
        ('enviado', 'Enviado'),
        ('recibido_parcial', 'Recibido Parcial'),
        ('recibido', 'Recibido Completo'),
        ('cancelado', 'Cancelado'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('normal', 'Normal'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='purchase_orders')
    tienda = models.ForeignKey(Tienda, on_delete=models.PROTECT, related_name='purchase_orders')
    numero_orden = models.CharField(max_length=50, unique=True, blank=True)
    
    # Enhanced date tracking
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_confirmacion = models.DateTimeField(null=True, blank=True, help_text="Cuando el proveedor confirmó la orden")
    fecha_estimada_entrega = models.DateField(null=True, blank=True, help_text="Fecha estimada de entrega")
    fecha_envio = models.DateTimeField(null=True, blank=True, help_text="Cuando el proveedor envió los productos")
    fecha_recepcion_parcial = models.DateTimeField(null=True, blank=True, help_text="Primera recepción parcial")
    fecha_recepcion_completa = models.DateTimeField(null=True, blank=True, help_text="Recepción completa")
    fecha_vencimiento = models.DateField(null=True, blank=True, help_text="Fecha límite para recibir")
    
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='normal')
      # Financial tracking
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    anticipo_requerido = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    anticipo_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Additional tracking
    numero_tracking = models.CharField(max_length=100, blank=True, help_text="Número de seguimiento del envío")
    observaciones = models.TextField(blank=True)
    archivos_adjuntos = models.JSONField(default=list, blank=True, help_text="URLs de archivos adjuntos")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(get_user_model(), related_name='purchase_orders_creadas', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(get_user_model(), related_name='purchase_orders_actualizadas', on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.numero_orden:
            # Generate order number
            last_order = PurchaseOrder.objects.filter(
                numero_orden__startswith=f'PO-{timezone.now().year}'
            ).order_by('-numero_orden').first()
            
            if last_order and last_order.numero_orden:
                last_num = int(last_order.numero_orden.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.numero_orden = f'PO-{timezone.now().year}-{new_num:06d}'
        
        super().save(*args, **kwargs)

    @property
    def dias_desde_creacion(self):
        """Días transcurridos desde la creación"""
        return (timezone.now().date() - self.fecha_creacion.date()).days
    
    @property
    def esta_atrasada(self):
        """Verifica si la orden está atrasada"""
        if not self.fecha_estimada_entrega:
            return False
        return timezone.now().date() > self.fecha_estimada_entrega and self.estado not in ['recibido', 'cancelado']
    
    @property
    def porcentaje_completado(self):
        """Calcula el porcentaje de items recibidos"""
        from .models import PurchaseOrderItem  # Import to avoid circular import issues
        total_items = PurchaseOrderItem.objects.filter(purchase_order=self).count()
        if total_items == 0:
            return 0
        
        completed_items = PurchaseOrderItem.objects.filter(
            purchase_order=self,
            cantidad_recibida__gte=models.F('cantidad_solicitada')
        ).count()
        return (completed_items / total_items) * 100

    def __str__(self):
        return f"{self.numero_orden} ({self.proveedor.nombre}) - {self.estado}"

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey('productos.Producto', on_delete=models.PROTECT, related_name='purchase_order_items') # Use string reference
    cantidad_solicitada = models.PositiveIntegerField()
    cantidad_recibida = models.PositiveIntegerField(default=0)
    cantidad_defectuosa = models.PositiveIntegerField(default=0, help_text="Cantidad recibida con defectos")
      # Enhanced item tracking
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    descuento_aplicado = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text="Descuento en porcentaje")
    fecha_recepcion = models.DateTimeField(null=True, blank=True)
    lote_proveedor = models.CharField(max_length=100, blank=True, help_text="Número de lote del proveedor")
    observaciones_item = models.TextField(blank=True)
    
    detalle_requisicion = models.ForeignKey(DetalleRequisicion, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_order_items')

    @property
    def cantidad_pendiente(self):
        """Cantidad que aún falta por recibir"""
        return max(0, self.cantidad_solicitada - self.cantidad_recibida)
    
    @property
    def esta_completo(self):
        """Verifica si el item está completamente recibido"""
        return self.cantidad_recibida >= self.cantidad_solicitada
    
    @property
    def subtotal(self):
        """Calcula el subtotal del item"""
        precio_con_descuento = self.precio_unitario * (1 - self.descuento_aplicado / 100)
        return self.cantidad_solicitada * precio_con_descuento
    
    @property
    def porcentaje_recibido(self):
        """Porcentaje de cantidad recibida"""
        if self.cantidad_solicitada == 0:
            return 0
        return (self.cantidad_recibida / self.cantidad_solicitada) * 100

    def __str__(self):
        return f"{self.producto.codigo} x {self.cantidad_solicitada} ({self.purchase_order.numero_orden})"


class PurchaseOrderTracking(models.Model):
    """Seguimiento detallado de cambios en órdenes de compra"""
    ACCION_CHOICES = [
        ('creada', 'Orden Creada'),
        ('confirmada', 'Confirmada por Proveedor'),
        ('modificada', 'Modificada'),
        ('enviada', 'Enviada por Proveedor'),
        ('recepcion_parcial', 'Recepción Parcial'),
        ('recepcion_completa', 'Recepción Completa'),
        ('cancelada', 'Cancelada'),
        ('devolucion', 'Devolución'),
    ]
    
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='tracking_history')
    accion = models.CharField(max_length=20, choices=ACCION_CHOICES)
    fecha = models.DateTimeField(default=timezone.now)
    usuario = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    descripcion = models.TextField()
    datos_adicionales = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.purchase_order.numero_orden} - {self.accion} ({self.fecha.strftime('%d/%m/%Y %H:%M')})"


class ProveedorEvaluacion(models.Model):
    """Evaluación periódica de proveedores"""
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='evaluaciones')
    periodo_inicio = models.DateField()
    periodo_fin = models.DateField()
    
    # Métricas de evaluación
    ordenes_totales = models.PositiveIntegerField(default=0)
    ordenes_a_tiempo = models.PositiveIntegerField(default=0)
    ordenes_atrasadas = models.PositiveIntegerField(default=0)
    productos_defectuosos = models.PositiveIntegerField(default=0)
    productos_recibidos = models.PositiveIntegerField(default=0)
      # Calificaciones
    calificacion_calidad = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('5.0'))
    calificacion_puntualidad = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('5.0'))
    calificacion_comunicacion = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('5.0'))
    calificacion_precio = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('5.0'))
    
    observaciones = models.TextField(blank=True)
    recomendaciones = models.TextField(blank=True)
    
    evaluado_por = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    fecha_evaluacion = models.DateTimeField(auto_now_add=True)
    
    @property
    def calificacion_promedio(self):
        """Calificación promedio de todas las métricas"""
        return (
            self.calificacion_calidad + 
            self.calificacion_puntualidad + 
            self.calificacion_comunicacion + 
            self.calificacion_precio
        ) / 4
    
    @property
    def porcentaje_puntualidad(self):
        """Porcentaje de órdenes entregadas a tiempo"""
        if self.ordenes_totales == 0:
            return 0
        return (self.ordenes_a_tiempo / self.ordenes_totales) * 100
    
    @property
    def porcentaje_calidad(self):
        """Porcentaje de productos sin defectos"""
        if self.productos_recibidos == 0:
            return 100
        return ((self.productos_recibidos - self.productos_defectuosos) / self.productos_recibidos) * 100
    
    class Meta:
        unique_together = ('proveedor', 'periodo_inicio', 'periodo_fin')
        ordering = ['-fecha_evaluacion']
    
    def __str__(self):
        return f"Evaluación {self.proveedor.nombre} ({self.periodo_inicio} - {self.periodo_fin})"
