"""
Factories para generar datos de prueba usando factory_boy
"""
import factory
from factory.django import DjangoModelFactory
from factory import fuzzy
from decimal import Decimal
import random
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from tiendas.models import Tienda
from productos.models import Producto, Catalogo
from clientes.models import Cliente, Anticipo, DescuentoCliente
from proveedores.models import Proveedor, PurchaseOrder, PurchaseOrderItem
from ventas.models import Pedido, DetallePedido
from inventario.models import Inventario, Traspaso, TraspasoItem
from caja.models import Caja, TransaccionCaja, Factura, NotaCargo
from administracion.models import LogAuditoria, PerfilUsuario, ConfiguracionSistema
from devoluciones.models import Devolucion
from descuentos.models import TabuladorDescuento

User = get_user_model()


# =============================================================================
# USER & AUTH FACTORIES
# =============================================================================

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    is_active = True
    is_staff = False
    is_superuser = False
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        password = extracted or 'testpass123'
        self.set_password(password)
        self.save()


class AdminUserFactory(UserFactory):
    is_staff = True
    is_superuser = True
    username = factory.Sequence(lambda n: f"admin{n}")


# =============================================================================
# CORE BUSINESS FACTORIES
# =============================================================================

class TiendaFactory(DjangoModelFactory):
    class Meta:
        model = Tienda
    
    nombre = factory.Faker('company')
    direccion = factory.Faker('address')
    contacto = factory.Faker('phone_number')
    activa = True


class ProveedorFactory(DjangoModelFactory):
    class Meta:
        model = Proveedor
    
    nombre = factory.Faker('company')
    contacto = factory.Faker('email')
    requiere_anticipo = False
    max_return_days = 0
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute('created_by')


class CatalogoFactory(DjangoModelFactory):
    class Meta:
        model = Catalogo
    
    nombre = factory.Sequence(lambda n: f"Catálogo {n}")
    temporada = factory.Faker('random_element', elements=('Primavera', 'Verano', 'Otoño', 'Invierno'))
    es_oferta = False
    activo = True
    fecha_inicio_vigencia = factory.LazyFunction(lambda: timezone.now().date())
    fecha_fin_vigencia = factory.LazyFunction(lambda: (timezone.now() + timedelta(days=90)).date())


class ProductoFactory(DjangoModelFactory):
    class Meta:
        model = Producto
    
    codigo = factory.Sequence(lambda n: f"PROD{n:05d}")
    marca = factory.Faker('random_element', elements=('Nike', 'Adidas', 'Puma', 'Reebok', 'Converse'))
    modelo = factory.Faker('random_element', elements=('Classic', 'Sport', 'Casual', 'Formal', 'Running'))
    color = factory.Faker('random_element', elements=('Negro', 'Blanco', 'Azul', 'Rojo', 'Verde'))
    propiedad = factory.Faker('random_element', elements=('38', '39', '40', '41', '42', '43'))
    costo = fuzzy.FuzzyDecimal(50.00, 500.00, 2)
    precio = factory.LazyAttribute(lambda obj: obj.costo * Decimal('1.5'))  # 50% markup
    numero_pagina = factory.Faker('random_int', min=1, max=100)
    temporada = factory.Faker('random_element', elements=('Primavera', 'Verano', 'Otoño', 'Invierno'))
    oferta = False
    admite_devolucion = True
    stock_minimo = 5
    proveedor = factory.SubFactory(ProveedorFactory)
    tienda = factory.SubFactory(TiendaFactory)
    catalogo = factory.SubFactory(CatalogoFactory)
    created_by = factory.SubFactory(UserFactory)


class ClienteFactory(DjangoModelFactory):
    class Meta:
        model = Cliente
    
    nombre = factory.Faker('name')
    contacto = factory.Faker('phone_number')
    observaciones = factory.Faker('text', max_nb_chars=200)
    saldo_a_favor = Decimal('0.00')
    monto_acumulado = Decimal('0.00')
    tienda = factory.SubFactory(TiendaFactory)
    max_return_days = 30
    puntos_lealtad = 0
    created_by = factory.SubFactory(UserFactory)


# =============================================================================
# SALES & ORDERS FACTORIES
# =============================================================================

class PedidoFactory(DjangoModelFactory):
    class Meta:
        model = Pedido
    
    cliente = factory.SubFactory(ClienteFactory)
    fecha = factory.LazyFunction(timezone.now)
    estado = 'pendiente'
    total = Decimal('0.00')  # Se calculará en post_generation
    tienda = factory.SelfAttribute('cliente.tienda')
    tipo = 'venta'
    descuento_aplicado = Decimal('0.00')
    pagado = False
    created_by = factory.SubFactory(UserFactory)


class DetallePedidoFactory(DjangoModelFactory):
    class Meta:
        model = DetallePedido
    
    pedido = factory.SubFactory(PedidoFactory)
    producto = factory.SubFactory(ProductoFactory)
    cantidad = fuzzy.FuzzyInteger(1, 5)
    precio_unitario = factory.SelfAttribute('producto.precio')
    subtotal = factory.LazyAttribute(lambda obj: obj.cantidad * obj.precio_unitario)


# =============================================================================
# INVENTORY FACTORIES
# =============================================================================

class InventarioFactory(DjangoModelFactory):
    class Meta:
        model = Inventario
    
    producto = factory.SubFactory(ProductoFactory)
    tienda = factory.SelfAttribute('producto.tienda')
    cantidad_actual = fuzzy.FuzzyInteger(10, 100)
    created_by = factory.SubFactory(UserFactory)


class TraspasoFactory(DjangoModelFactory):
    class Meta:
        model = Traspaso
    
    tienda_origen = factory.SubFactory(TiendaFactory)
    tienda_destino = factory.SubFactory(TiendaFactory)
    estado = 'pendiente'
    created_by = factory.SubFactory(UserFactory)


class TraspasoItemFactory(DjangoModelFactory):
    class Meta:
        model = TraspasoItem
    
    traspaso = factory.SubFactory(TraspasoFactory)
    producto = factory.SubFactory(ProductoFactory)
    cantidad = fuzzy.FuzzyInteger(1, 10)


# =============================================================================
# CASH BOX FACTORIES
# =============================================================================

class CajaFactory(DjangoModelFactory):
    class Meta:
        model = Caja
    
    tienda = factory.SubFactory(TiendaFactory)
    fecha = factory.LazyFunction(timezone.now)
    fondo_inicial = Decimal('1000.00')
    ingresos = Decimal('0.00')
    egresos = Decimal('0.00')
    saldo_final = Decimal('1000.00')
    cerrada = False
    created_by = factory.SubFactory(UserFactory)


class TransaccionCajaFactory(DjangoModelFactory):
    class Meta:
        model = TransaccionCaja
    
    caja = factory.SubFactory(CajaFactory)
    tipo_movimiento = 'INGRESO'
    monto = fuzzy.FuzzyDecimal(10.00, 1000.00, 2)
    descripcion = factory.Faker('sentence', nb_words=4)
    referencia = factory.Faker('uuid4')
    created_by = factory.SubFactory(UserFactory)


class FacturaFactory(DjangoModelFactory):
    class Meta:
        model = Factura
    
    pedido = factory.SubFactory(PedidoFactory)
    folio = factory.Sequence(lambda n: f"FAC{n:06d}")
    fecha = factory.LazyFunction(lambda: timezone.now().date())
    total = factory.SelfAttribute('pedido.total')
    created_by = factory.SubFactory(UserFactory)


# =============================================================================
# ADMINISTRATION FACTORIES
# =============================================================================

class LogAuditoriaFactory(DjangoModelFactory):
    class Meta:
        model = LogAuditoria
    
    usuario = factory.SubFactory(UserFactory)
    accion = factory.Faker('random_element', elements=[choice[0] for choice in LogAuditoria.ACCION_CHOICES])
    descripcion = factory.Faker('sentence')
    modelo_afectado = factory.Faker('random_element', elements=['Producto', 'Cliente', 'Pedido', 'Inventario'])
    objeto_id = factory.Faker('random_int', min=1, max=1000)
    ip_address = factory.Faker('ipv4')
    user_agent = factory.Faker('user_agent')


class PerfilUsuarioFactory(DjangoModelFactory):
    class Meta:
        model = PerfilUsuario
    
    usuario = factory.SubFactory(UserFactory)
    telefono = factory.Sequence(lambda n: f"55{n:08d}")  # Generate phone numbers like 5500000001
    tienda_asignada = factory.SubFactory(TiendaFactory)
    fecha_ultimo_acceso = None
    intentos_login_fallidos = 0
    cuenta_bloqueada = False
    fecha_bloqueo = None
    requiere_cambio_password = False


class ConfiguracionSistemaFactory(DjangoModelFactory):
    class Meta:
        model = ConfiguracionSistema
    
    clave = factory.Sequence(lambda n: f"config_key_{n}")
    valor = factory.Faker('word')
    descripcion = factory.Faker('sentence')
    tipo_dato = 'string'
    modificado_por = factory.SubFactory(UserFactory)




# =============================================================================
# PURCHASE ORDER FACTORIES
# =============================================================================

class PurchaseOrderFactory(DjangoModelFactory):
    class Meta:
        model = PurchaseOrder
    
    proveedor = factory.SubFactory(ProveedorFactory)
    tienda = factory.SubFactory(TiendaFactory)
    estado = 'pendiente'
    created_by = factory.SubFactory(UserFactory)


class PurchaseOrderItemFactory(DjangoModelFactory):
    class Meta:
        model = PurchaseOrderItem
    
    purchase_order = factory.SubFactory(PurchaseOrderFactory)
    producto = factory.SubFactory(ProductoFactory)
    cantidad_solicitada = factory.Faker('random_int', min=1, max=100)
    cantidad_recibida = 0


# =============================================================================
# RETURNS/DEVOLUCIONES FACTORIES
# =============================================================================

class DevolucionFactory(DjangoModelFactory):
    class Meta:
        model = Devolucion
    
    cliente = factory.SubFactory(ClienteFactory)
    producto = factory.SubFactory(ProductoFactory)
    detalle_pedido = None
    tipo = fuzzy.FuzzyChoice(['defecto', 'cambio'])
    motivo = factory.Faker('sentence', nb_words=6)
    estado = 'pendiente'
    confirmacion_proveedor = False
    afecta_inventario = True
    saldo_a_favor_generado = Decimal('0.00')
    precio_devolucion = fuzzy.FuzzyDecimal(100.00, 1000.00, 2)
    created_by = factory.SubFactory(UserFactory)


# =============================================================================
# DISCOUNT FACTORIES
# =============================================================================

class TabuladorDescuentoFactory(DjangoModelFactory):
    class Meta:
        model = TabuladorDescuento
    
    rango_min = factory.LazyFunction(lambda: Decimal(random.randint(0, 1000)))
    rango_max = factory.LazyAttribute(lambda obj: obj.rango_min + Decimal('500.00'))
    porcentaje = factory.LazyFunction(lambda: Decimal(random.randint(1, 20)))


# =============================================================================
# CLIENT RELATED FACTORIES
# =============================================================================

class AnticipoFactory(DjangoModelFactory):
    class Meta:
        model = Anticipo
    
    cliente = factory.SubFactory(ClienteFactory)
    monto = fuzzy.FuzzyDecimal(100.00, 5000.00, 2)
    fecha = factory.LazyFunction(lambda: timezone.now().date())
    created_by = factory.SubFactory(UserFactory)


class DescuentoClienteFactory(DjangoModelFactory):
    class Meta:
        model = DescuentoCliente
    
    cliente = factory.SubFactory(ClienteFactory)
    porcentaje = fuzzy.FuzzyDecimal(5.00, 25.00, 2)
    mes_vigente = factory.LazyFunction(lambda: timezone.now().strftime("%Y-%m"))
    monto_acumulado_mes_anterior = fuzzy.FuzzyDecimal(0.00, 10000.00, 2)
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)


# =============================================================================
# UTILITY FACTORIES PARA CREAR ESCENARIOS COMPLEJOS
# =============================================================================

class PedidoCompletoFactory(PedidoFactory):
    """Factory para crear un pedido con detalles automáticamente"""
    
    @factory.post_generation
    def create_detalles(self, create, extracted, **kwargs):
        if not create:
            return
        
        # Crear entre 1 y 3 detalles
        num_detalles = extracted or 3
        total = Decimal('0.00')
        
        for _ in range(num_detalles):
            detalle = DetallePedidoFactory(pedido=self)
            total += detalle.subtotal
        
        # Actualizar el total del pedido
        self.total = total
        self.save()


class TiendaConInventarioFactory(TiendaFactory):
    """Factory para crear una tienda con productos e inventario"""
    
    @factory.post_generation
    def create_inventario(self, create, extracted, **kwargs):
        if not create:
            return
        
        # Crear productos con inventario
        num_productos = extracted or 5
        
        for _ in range(num_productos):
            producto = ProductoFactory(tienda=self)
            InventarioFactory(producto=producto, tienda=self)


class CajaAbiertaFactory(CajaFactory):
    """Factory para crear una caja abierta lista para operaciones"""
    cerrada = False
    ingresos = Decimal('0.00')
    egresos = Decimal('0.00')
    saldo_final = factory.SelfAttribute('fondo_inicial')


# Alias for compatibility
MovimientoCajaFactory = TransaccionCajaFactory

# =============================================================================
# NOTE CARGO FACTORY
# =============================================================================

class NotaCargoFactory(DjangoModelFactory):
    class Meta:
        model = NotaCargo
    
    caja = factory.SubFactory(CajaFactory)
    monto = fuzzy.FuzzyDecimal(10.00, 500.00, 2)
    motivo = factory.Faker('sentence', nb_words=4)
    fecha = factory.LazyFunction(lambda: timezone.now().date())
    created_by = factory.SubFactory(UserFactory)
