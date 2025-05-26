from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, datetime, timedelta
import random

from tiendas.models import Tienda
from proveedores.models import Proveedor
from productos.models import Catalogo, Producto
from clientes.models import Cliente, Anticipo, DescuentoCliente
from inventario.models import Inventario
from ventas.models import Pedido, DetallePedido
from caja.models import Caja, TransaccionCaja

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with sample data for Pronto Shoes POS system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self.clear_data()

        self.stdout.write('Starting database population...')
        
        with transaction.atomic():
            # Create admin user if not exists
            admin_user = self.create_admin_user()
            
            # Create stores
            tiendas = self.create_tiendas(admin_user)
            
            # Create suppliers
            proveedores = self.create_proveedores(admin_user)
            
            # Create catalogs
            catalogos = self.create_catalogos()
            
            # Create products
            productos = self.create_productos(proveedores, tiendas, catalogos, admin_user)
            
            # Create inventory
            self.create_inventario(productos, tiendas, admin_user)
            
            # Create customers
            clientes = self.create_clientes(tiendas, admin_user)
            
            # Create orders and sales
            self.create_pedidos(clientes, productos, tiendas, admin_user)
              # Create cash register data
            self.create_cajas(tiendas, admin_user)

        self.stdout.write(
            self.style.SUCCESS('Successfully populated database with sample data!')
        )

    def clear_data(self):
        """Clear existing data"""
        # Import models that might have dependencies
        try:
            from caja.models import Factura
            from devoluciones.models import Devolucion
            from requisiciones.models import Requisicion, DetalleRequisicion
            from proveedores.models import PurchaseOrder, PurchaseOrderItem
        except ImportError:
            pass
        
        # Clear in dependency order
        models_to_clear = [
            # First clear dependent models
            ('Factura', lambda: Factura.objects.all().delete() if 'Factura' in locals() else None),
            ('Devolucion', lambda: Devolucion.objects.all().delete() if 'Devolucion' in locals() else None),
            ('PurchaseOrderItem', lambda: PurchaseOrderItem.objects.all().delete() if 'PurchaseOrderItem' in locals() else None),
            ('PurchaseOrder', lambda: PurchaseOrder.objects.all().delete() if 'PurchaseOrder' in locals() else None),
            ('DetalleRequisicion', lambda: DetalleRequisicion.objects.all().delete() if 'DetalleRequisicion' in locals() else None),
            ('Requisicion', lambda: Requisicion.objects.all().delete() if 'Requisicion' in locals() else None),
            
            # Then clear main models
            ('DetallePedido', lambda: DetallePedido.objects.all().delete()),
            ('Pedido', lambda: Pedido.objects.all().delete()),
            ('TransaccionCaja', lambda: TransaccionCaja.objects.all().delete()),
            ('Caja', lambda: Caja.objects.all().delete()),
            ('Inventario', lambda: Inventario.objects.all().delete()),
            ('Producto', lambda: Producto.objects.all().delete()),
            ('Catalogo', lambda: Catalogo.objects.all().delete()),
            ('DescuentoCliente', lambda: DescuentoCliente.objects.all().delete()),
            ('Anticipo', lambda: Anticipo.objects.all().delete()),
            ('Cliente', lambda: Cliente.objects.all().delete()),
            ('Proveedor', lambda: Proveedor.objects.all().delete()),
            ('Tienda', lambda: Tienda.objects.all().delete()),
        ]
        
        for model_name, delete_func in models_to_clear:
            try:
                delete_func()
                self.stdout.write(f'Cleared {model_name}')
            except Exception as e:
                self.stdout.write(f'Warning: Could not clear {model_name}: {e}')

    def create_admin_user(self):
        """Create admin user if not exists"""
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@prontoshoes.com',
                'first_name': 'Administrador',
                'last_name': 'Sistema',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('Created admin user')
        else:
            self.stdout.write('Admin user already exists')
        
        return admin_user

    def create_tiendas(self, admin_user):
        """Create sample stores"""
        tiendas_data = [
            {
                'nombre': 'Pronto Shoes Centro',
                'direccion': 'Av. Juárez 123, Centro, Ciudad de México',
                'contacto': '55-1234-5678',
                'activa': True
            },
            {
                'nombre': 'Pronto Shoes Norte',
                'direccion': 'Av. Insurgentes Norte 456, Gustavo A. Madero, CDMX',
                'contacto': '55-8765-4321',
                'activa': True
            },
            {
                'nombre': 'Pronto Shoes Sur',
                'direccion': 'Calz. de Tlalpan 789, Xochimilco, CDMX',
                'contacto': '55-9876-5432',
                'activa': True
            }
        ]
        
        tiendas = []
        for tienda_data in tiendas_data:
            tienda, created = Tienda.objects.get_or_create(
                nombre=tienda_data['nombre'],
                defaults={
                    **tienda_data,
                    'created_by': admin_user,
                    'updated_by': admin_user
                }
            )
            tiendas.append(tienda)
            if created:
                self.stdout.write(f'Created store: {tienda.nombre}')
        
        return tiendas

    def create_proveedores(self, admin_user):
        """Create sample suppliers"""
        proveedores_data = [
            {
                'nombre': 'Calzado Industrial López',
                'contacto': 'contacto@cil.com.mx',
                'requiere_anticipo': True,
                'max_return_days': 15
            },
            {
                'nombre': 'Distribuidora de Calzado González',
                'contacto': 'ventas@dcg.mx',
                'requiere_anticipo': False,
                'max_return_days': 30
            },
            {
                'nombre': 'Fabricantes Unidos del Calzado',
                'contacto': 'info@fuc.com',
                'requiere_anticipo': True,
                'max_return_days': 10
            },
            {
                'nombre': 'Calzado Premium Internacional',
                'contacto': 'importaciones@cpi.mx',
                'requiere_anticipo': False,
                'max_return_days': 45
            },
            {
                'nombre': 'Zapaterías del Bajío',
                'contacto': 'distribución@zdb.com.mx',
                'requiere_anticipo': True,
                'max_return_days': 20
            }
        ]
        
        proveedores = []
        for proveedor_data in proveedores_data:
            proveedor, created = Proveedor.objects.get_or_create(
                nombre=proveedor_data['nombre'],
                defaults={
                    **proveedor_data,
                    'created_by': admin_user,
                    'updated_by': admin_user
                }
            )
            proveedores.append(proveedor)
            if created:
                self.stdout.write(f'Created supplier: {proveedor.nombre}')
        
        return proveedores

    def create_catalogos(self):
        """Create sample catalogs"""
        catalogos_data = [
            {
                'nombre': 'Catálogo Primavera-Verano 2024',
                'temporada': 'Primavera-Verano',
                'es_oferta': False,
                'activo': True,
                'fecha_inicio_vigencia': date(2024, 3, 1),
                'fecha_fin_vigencia': date(2024, 8, 31)
            },
            {
                'nombre': 'Catálogo Otoño-Invierno 2024',
                'temporada': 'Otoño-Invierno',
                'es_oferta': False,
                'activo': False,
                'fecha_inicio_vigencia': date(2024, 9, 1),
                'fecha_fin_vigencia': date(2025, 2, 28)
            },
            {
                'nombre': 'Ofertas Especiales Mayo 2024',
                'temporada': None,
                'es_oferta': True,
                'activo': True,
                'fecha_inicio_vigencia': date(2024, 5, 1),
                'fecha_fin_vigencia': date(2024, 5, 31)
            },
            {
                'nombre': 'Liquidación Fin de Temporada',
                'temporada': 'Primavera-Verano',
                'es_oferta': True,
                'activo': False,
                'fecha_inicio_vigencia': date(2024, 8, 15),
                'fecha_fin_vigencia': date(2024, 8, 31)
            }
        ]
        
        catalogos = []
        for catalogo_data in catalogos_data:
            catalogo, created = Catalogo.objects.get_or_create(
                nombre=catalogo_data['nombre'],
                defaults=catalogo_data
            )
            catalogos.append(catalogo)
            if created:
                self.stdout.write(f'Created catalog: {catalogo.nombre}')
        
        return catalogos

    def create_productos(self, proveedores, tiendas, catalogos, admin_user):
        """Create sample products"""
        marcas = ['Nike', 'Adidas', 'Puma', 'Reebok', 'Converse', 'Vans', 'New Balance', 'Fila']
        modelos = ['Runner', 'Classic', 'Sport', 'Urban', 'Casual', 'Pro', 'Elite', 'Comfort']
        colores = ['Negro', 'Blanco', 'Azul', 'Rojo', 'Gris', 'Verde', 'Amarillo', 'Rosa']
        propiedades = ['24', '25', '26', '27', '28', '29', '30', '31', '32']
        temporadas = ['Primavera-Verano', 'Otoño-Invierno']
        
        productos = []
        
        # Create products for active catalogs
        active_catalogs = [c for c in catalogos if c.activo]
        
        for i in range(100):  # Create 100 sample products
            marca = random.choice(marcas)
            modelo = random.choice(modelos)
            color = random.choice(colores)
            propiedad = random.choice(propiedades)
            
            # Generate unique code
            codigo = f"{marca[:3].upper()}-{modelo[:3].upper()}-{i+1:04d}"
            
            # Random prices
            costo = Decimal(str(random.uniform(200, 800)))
            precio = costo * Decimal('1.5')  # 50% markup
            
            # Random catalog selection
            catalogo = random.choice(active_catalogs) if active_catalogs else None
            
            producto_data = {
                'codigo': codigo,
                'marca': marca,
                'modelo': modelo,
                'color': color,
                'propiedad': propiedad,
                'costo': costo.quantize(Decimal('0.01')),
                'precio': precio.quantize(Decimal('0.01')),
                'numero_pagina': str(random.randint(1, 200)),
                'temporada': random.choice(temporadas),
                'oferta': random.choice([True, False]),
                'admite_devolucion': True,
                'stock_minimo': random.randint(5, 20),
                'proveedor': random.choice(proveedores),
                'tienda': random.choice(tiendas),
                'catalogo': catalogo,
                'created_by': admin_user,
                'updated_by': admin_user
            }
            
            try:
                producto, created = Producto.objects.get_or_create(
                    codigo=codigo,
                    defaults=producto_data
                )
                productos.append(producto)
                if created:
                    self.stdout.write(f'Created product: {producto.codigo} - {producto.marca} {producto.modelo}')
            except Exception as e:
                self.stdout.write(f'Error creating product {codigo}: {e}')
        
        return productos

    def create_inventario(self, productos, tiendas, admin_user):
        """Create sample inventory"""
        for producto in productos:
            for tienda in tiendas:
                # Random stock levels
                cantidad_actual = random.randint(0, 50)
                
                inventario_data = {
                    'tienda': tienda,
                    'producto': producto,
                    'cantidad_actual': cantidad_actual,
                    'created_by': admin_user,
                    'updated_by': admin_user
                }
                
                inventario, created = Inventario.objects.get_or_create(
                    tienda=tienda,
                    producto=producto,
                    defaults=inventario_data
                )
                
                if created:
                    self.stdout.write(f'Created inventory: {producto.codigo} in {tienda.nombre} - {cantidad_actual} units')

    def create_clientes(self, tiendas, admin_user):
        """Create sample customers"""
        clientes_data = [
            {
                'nombre': 'Distribuidora El Zapato Feliz',
                'contacto': 'Maria González - 55-1111-2222',
                'observaciones': 'Cliente frecuente, siempre paga a tiempo',
                'saldo_a_favor': Decimal('1500.00'),
                'monto_acumulado': Decimal('25000.00'),
                'max_return_days': 30,
                'puntos_lealtad': 250
            },
            {
                'nombre': 'Calzados y Más SA de CV',
                'contacto': 'Juan Pérez - 55-3333-4444',
                'observaciones': 'Compras grandes, solicita descuentos por volumen',
                'saldo_a_favor': Decimal('2200.00'),
                'monto_acumulado': Decimal('45000.00'),
                'max_return_days': 45,
                'puntos_lealtad': 450
            },
            {
                'nombre': 'Boutique de Calzado Luna',
                'contacto': 'Ana Martínez - 55-5555-6666',
                'observaciones': 'Prefiere productos de marca premium',
                'saldo_a_favor': Decimal('800.00'),
                'monto_acumulado': Decimal('18000.00'),
                'max_return_days': 15,
                'puntos_lealtad': 180
            },
            {
                'nombre': 'Zapaterías del Centro',
                'contacto': 'Carlos López - 55-7777-8888',
                'observaciones': 'Cliente nuevo, evaluar comportamiento de pago',
                'saldo_a_favor': Decimal('0.00'),
                'monto_acumulado': Decimal('5000.00'),
                'max_return_days': 30,
                'puntos_lealtad': 50
            },
            {
                'nombre': 'Distribuidora Popular',
                'contacto': 'Rosa Hernández - 55-9999-0000',
                'observaciones': 'Volumen alto, buenos pagos, cliente preferente',
                'saldo_a_favor': Decimal('3500.00'),
                'monto_acumulado': Decimal('65000.00'),
                'max_return_days': 60,
                'puntos_lealtad': 650
            }
        ]
        
        clientes = []
        for cliente_data in clientes_data:
            tienda = random.choice(tiendas)
            cliente, created = Cliente.objects.get_or_create(
                nombre=cliente_data['nombre'],
                defaults={
                    **cliente_data,
                    'tienda': tienda,
                    'created_by': admin_user,
                    'updated_by': admin_user
                }
            )
            clientes.append(cliente)
            if created:
                self.stdout.write(f'Created customer: {cliente.nombre}')
                
                # Create some advance payments for customers
                if cliente_data['saldo_a_favor'] > 0:
                    anticipo = Anticipo.objects.create(
                        cliente=cliente,
                        monto=cliente_data['saldo_a_favor'],
                        fecha=date.today() - timedelta(days=random.randint(1, 30))
                    )
                    self.stdout.write(f'Created advance payment for {cliente.nombre}: ${anticipo.monto}')
        
        return clientes

    def create_pedidos(self, clientes, productos, tiendas, admin_user):
        """Create sample orders"""
        for i in range(20):  # Create 20 sample orders
            cliente = random.choice(clientes)
            tienda = random.choice(tiendas)
            
            # Create order
            fecha = datetime.now() - timedelta(days=random.randint(1, 90))
            estado = random.choice(['pendiente', 'surtido', 'cancelado'])
            tipo = random.choice(['preventivo', 'venta'])
            descuento_aplicado = Decimal(str(random.uniform(0, 15)))
            pagado = random.choice([True, False])
            
            pedido = Pedido.objects.create(
                cliente=cliente,
                fecha=fecha,
                estado=estado,
                total=Decimal('0.00'),  # Will be calculated after adding items
                tienda=tienda,
                tipo=tipo,
                descuento_aplicado=descuento_aplicado,
                pagado=pagado,
                created_by=admin_user,
                updated_by=admin_user
            )
            
            # Add order items
            total = Decimal('0.00')
            num_items = random.randint(1, 5)
            
            for j in range(num_items):
                producto = random.choice(productos)
                cantidad = random.randint(1, 10)
                precio_unitario = producto.precio
                subtotal = precio_unitario * cantidad
                
                DetallePedido.objects.create(
                    pedido=pedido,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    subtotal=subtotal
                )
                
                total += subtotal
            
            # Apply discount and update total
            if descuento_aplicado > 0:
                total = total * (1 - descuento_aplicado / 100)
            
            pedido.total = total.quantize(Decimal('0.01'))
            pedido.save()
            
            self.stdout.write(f'Created order {pedido.id} for {cliente.nombre}: ${pedido.total}')

    def create_cajas(self, tiendas, admin_user):
        """Create sample cash register data"""
        # Create cash registers for the last 30 days
        for tienda in tiendas:
            for i in range(30):
                fecha = date.today() - timedelta(days=i)
                
                # Random cash flow
                fondo_inicial = Decimal(str(random.uniform(1000, 5000)))
                ingresos = Decimal(str(random.uniform(2000, 15000)))
                egresos = Decimal(str(random.uniform(500, 3000)))
                saldo_final = fondo_inicial + ingresos - egresos
                
                # Older records are more likely to be closed
                cerrada = i > 7 or random.choice([True, False])
                
                caja, created = Caja.objects.get_or_create(
                    tienda=tienda,
                    fecha=fecha,
                    defaults={
                        'fondo_inicial': fondo_inicial.quantize(Decimal('0.01')),
                        'ingresos': ingresos.quantize(Decimal('0.01')),
                        'egresos': egresos.quantize(Decimal('0.01')),
                        'saldo_final': saldo_final.quantize(Decimal('0.01')),
                        'cerrada': cerrada,
                        'created_by': admin_user,
                        'updated_by': admin_user
                    }
                )
                
                if created:
                    self.stdout.write(f'Created cash register for {tienda.nombre} on {fecha}: ${saldo_final}')
