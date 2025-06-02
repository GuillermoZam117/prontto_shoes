from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from clientes.models import Cliente
from ventas.models import Pedido, DetallePedido
from productos.models import Producto
from proveedores.models import Proveedor

User = get_user_model()

class OrdenCliente(models.Model):
    """
    Contenedor de múltiples pedidos por cliente.
    Permite acumulación y gestión avanzada de órdenes.
    """
    ESTADO_CHOICES = [
        ('ACTIVO', 'Activo - Recibiendo Productos'),
        ('PENDIENTE', 'Pendiente - Esperando Surtido'),
        ('VENTA', 'Completado - Convertido a Venta'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='ordenes_cliente')
    numero_orden = models.CharField(max_length=50, unique=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='ACTIVO')
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    
    # Métricas de la orden
    total_productos = models.PositiveIntegerField(default=0, help_text='Total de productos en la orden')
    productos_recibidos = models.PositiveIntegerField(default=0, help_text='Productos ya recibidos')
    monto_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    anticipos_pagados = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Información adicional
    observaciones = models.TextField(blank=True, null=True)
    
    # Metadatos
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordenes_creadas')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordenes_actualizadas')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Manager personalizado
    # objects = OrdenClienteManager()  # Se agregará después para evitar dependencias circulares
    
    class Meta:
        verbose_name = 'Orden de Cliente'
        verbose_name_plural = 'Órdenes de Cliente'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Orden {self.numero_orden} - {self.cliente.nombre}"
    
    @property
    def porcentaje_completado(self):
        """Calcula el porcentaje de completitud de la orden"""
        if self.total_productos == 0:
            return 0
        return (self.productos_recibidos * 100) / self.total_productos
    
    @property
    def esta_completa(self):
        """Verifica si la orden está completa"""
        return self.productos_recibidos >= self.total_productos and self.total_productos > 0


class EstadoProductoSeguimiento(models.Model):
    """
    Seguimiento detallado de estados de productos en pedidos.
    Permite tracking granular de cada producto.
    """
    ESTADOS_PRODUCTO = [
        ('APARTADO', 'Apartado en Pedido'),
        ('RECIBIDO', 'Recibido en Tienda'),
        ('SOLICITADO_PROVEEDOR', 'Solicitado a Proveedor'),
        ('VERIFICADO', 'Verificado por Proveedor'),
        ('EN_ESPERA', 'En Espera de Envío'),
        ('RECIBIDOS_TIENDA', 'Recibidos en Tienda'),
        ('LISTO_ENTREGA', 'Listo para Entrega'),
    ]
    
    detalle_pedido = models.ForeignKey(DetallePedido, on_delete=models.CASCADE, related_name='seguimientos')
    estado_anterior = models.CharField(max_length=50, blank=True, null=True)
    estado_nuevo = models.CharField(max_length=50, choices=ESTADOS_PRODUCTO)
    fecha_cambio = models.DateTimeField(default=timezone.now)
    usuario_cambio = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)
    ubicacion = models.CharField(max_length=100, blank=True, null=True, help_text='Ubicación física del producto')
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True, help_text='Proveedor relacionado con este cambio de estado')
    
    class Meta:
        verbose_name = 'Seguimiento de Estado'
        verbose_name_plural = 'Seguimientos de Estado'
        ordering = ['-fecha_cambio']
    
    def __str__(self):
        return f"{self.detalle_pedido.producto.codigo} -> {self.estado_nuevo}"


class EntregaParcial(models.Model):
    """
    Registro de entregas parciales de pedidos.
    Permite dividir pedidos y generar nuevos tickets.
    """
    pedido_original = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='entregas_parciales_originales')
    pedido_nuevo = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='entregas_parciales_nuevas', help_text='Nuevo pedido con productos restantes')
    ticket_entrega = models.CharField(max_length=50, unique=True, help_text='Ticket único para esta entrega parcial')
    fecha_entrega = models.DateTimeField(default=timezone.now)
    
    # Información de productos entregados (JSON para flexibilidad)
    productos_entregados = models.JSONField(help_text='Lista de productos entregados en esta entrega parcial')
    monto_entregado = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(max_length=50, blank=True, null=True)
    
    # Usuario y observaciones
    usuario_entrega = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Entrega Parcial'
        verbose_name_plural = 'Entregas Parciales'
        ordering = ['-fecha_entrega']
    
    def __str__(self):
        return f"Entrega {self.ticket_entrega} - Pedido {self.pedido_original.id}"


class NotaCredito(models.Model):
    """
    Gestión de notas de crédito y débito para clientes.
    Sistema automatizado con vencimiento a 60 días.
    """
    TIPO_CHOICES = [
        ('CREDITO', 'Nota de Crédito'),
        ('DEBITO', 'Nota de Débito'),
    ]
    
    ESTADO_CHOICES = [
        ('ACTIVA', 'Activa'),
        ('APLICADA', 'Aplicada'),
        ('VENCIDA', 'Vencida'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='notas_credito')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    motivo = models.TextField(help_text='Motivo de la nota de crédito/débito')
    
    # Relaciones con pedidos
    pedido_origen = models.ForeignKey(Pedido, on_delete=models.SET_NULL, null=True, blank=True, related_name='notas_origen', help_text='Pedido que originó esta nota')
    aplicada_en_pedido = models.ForeignKey(Pedido, on_delete=models.SET_NULL, null=True, blank=True, related_name='notas_aplicadas', help_text='Pedido donde se aplicó esta nota')
    
    # Fechas y estado
    fecha_vencimiento = models.DateField(help_text='Fecha de vencimiento (60 días por defecto)')
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='ACTIVA')
    fecha_aplicacion = models.DateTimeField(null=True, blank=True)
    
    # Metadatos
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Nota de Crédito/Débito'
        verbose_name_plural = 'Notas de Crédito/Débito'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_tipo_display()} {self.id} - {self.cliente.nombre} - ${self.monto}"
    
    @property
    def esta_vencida(self):
        """Verifica si la nota está vencida"""
        from django.utils import timezone
        return timezone.now().date() > self.fecha_vencimiento and self.estado == 'ACTIVA'
    
    def save(self, *args, **kwargs):
        """Override save para establecer fecha de vencimiento automática"""
        if not self.fecha_vencimiento:
            from datetime import timedelta
            self.fecha_vencimiento = timezone.now().date() + timedelta(days=60)
        super().save(*args, **kwargs)


class PortalClientePolitica(models.Model):
    """
    Gestión de contenido para el portal de cliente.
    Políticas, términos y FAQs.
    """
    TIPO_CHOICES = [
        ('POLITICA', 'Política'),
        ('TERMINO', 'Término y Condición'),
        ('FAQ', 'Pregunta Frecuente'),
    ]
    
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    activo = models.BooleanField(default=True)
    orden_display = models.PositiveIntegerField(default=0, help_text='Orden de visualización')
    fecha_vigencia = models.DateField(default=timezone.now)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Política de Portal'
        verbose_name_plural = 'Políticas de Portal'
        ordering = ['tipo', 'orden_display']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.titulo}"


class ProductoCompartir(models.Model):
    """
    Tracking de productos compartidos en redes sociales.
    Analytics de compartido por clientes.
    """
    PLATAFORMA_CHOICES = [
        ('FACEBOOK', 'Facebook'),
        ('WHATSAPP', 'WhatsApp'),
        ('INSTAGRAM', 'Instagram'),
        ('TWITTER', 'Twitter'),
    ]
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='compartidos')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='productos_compartidos')
    plataforma = models.CharField(max_length=15, choices=PLATAFORMA_CHOICES)
    url_compartida = models.URLField(blank=True, null=True)
    fecha_compartido = models.DateTimeField(default=timezone.now)
    clicks_generados = models.PositiveIntegerField(default=0, help_text='Clicks rastreados desde este compartido')
    
    class Meta:
        verbose_name = 'Producto Compartido'
        verbose_name_plural = 'Productos Compartidos'
        ordering = ['-fecha_compartido']
    
    def __str__(self):
        return f"{self.producto.codigo} compartido en {self.plataforma} por {self.cliente.nombre}"
