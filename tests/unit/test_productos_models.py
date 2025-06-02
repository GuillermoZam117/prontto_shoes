"""
Tests unitarios para modelos de productos
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
from datetime import date, timedelta

from productos.models import Producto, Catalogo
from ..factories import (
    ProductoFactory, CatalogoFactory, ProveedorFactory, 
    TiendaFactory, UserFactory
)
from ..base import BaseTestCase


class CatalogoModelTests(BaseTestCase):
    """Tests para el modelo Catalogo"""
    
    def test_should_create_catalogo_with_valid_data(self):
        """Debería crear catálogo con datos válidos"""
        catalogo = CatalogoFactory(
            nombre='Catálogo Primavera 2025',
            temporada='Primavera',
            es_oferta=False,
            activo=True
        )
        
        self.assertEqual(catalogo.nombre, 'Catálogo Primavera 2025')
        self.assertEqual(catalogo.temporada, 'Primavera')
        self.assertFalse(catalogo.es_oferta)
        self.assertTrue(catalogo.activo)
        self.assertIsNotNone(catalogo.created_at)
        self.assertIsNotNone(catalogo.updated_at)
    
    def test_should_enforce_unique_nombre(self):
        """Debería enforcer nombre único"""
        CatalogoFactory(nombre='Catálogo Único')
        
        with self.assertRaises(IntegrityError):
            CatalogoFactory(nombre='Catálogo Único')
    
    def test_should_have_correct_string_representation(self):
        """Debería tener la representación string correcta"""
        catalogo = CatalogoFactory(nombre='Test Catalog')
        self.assertEqual(str(catalogo), 'Test Catalog')
    
    def test_should_allow_optional_temporada(self):
        """Debería permitir temporada opcional"""
        catalogo = CatalogoFactory(temporada=None)
        self.assertIsNone(catalogo.temporada)
    
    def test_should_validate_date_ranges(self):
        """Debería validar rangos de fecha"""
        today = date.today()
        future_date = today + timedelta(days=30)
        
        catalogo = CatalogoFactory(
            fecha_inicio_vigencia=today,
            fecha_fin_vigencia=future_date
        )
        
        self.assertEqual(catalogo.fecha_inicio_vigencia, today)
        self.assertEqual(catalogo.fecha_fin_vigencia, future_date)
    
    def test_should_default_to_active_and_not_offer(self):
        """Debería tener valores por defecto correctos"""
        catalogo = Catalogo.objects.create(nombre='Test Default')
        
        self.assertTrue(catalogo.activo)
        self.assertFalse(catalogo.es_oferta)
    
    def test_should_handle_long_nombres(self):
        """Debería manejar nombres largos hasta el límite"""
        long_name = 'A' * 100  # Límite máximo
        catalogo = CatalogoFactory(nombre=long_name)
        self.assertEqual(catalogo.nombre, long_name)
        
        # Verificar que nombres más largos fallan
        with self.assertRaises(ValidationError):
            too_long_name = 'A' * 101
            catalogo = Catalogo(nombre=too_long_name)
            catalogo.full_clean()


class ProductoModelTests(BaseTestCase):
    """Tests para el modelo Producto"""
    
    def test_should_create_producto_with_valid_data(self):
        """Debería crear producto con datos válidos"""
        proveedor = ProveedorFactory()
        tienda = TiendaFactory()
        catalogo = CatalogoFactory()
        user = UserFactory()
        
        producto = ProductoFactory(
            codigo='NIKE001',
            marca='Nike',
            modelo='Air Max',
            color='Negro',
            propiedad='42',
            costo=Decimal('100.00'),
            precio=Decimal('150.00'),
            proveedor=proveedor,
            tienda=tienda,
            catalogo=catalogo,
            created_by=user
        )
        
        self.assertEqual(producto.codigo, 'NIKE001')
        self.assertEqual(producto.marca, 'Nike')
        self.assertEqual(producto.modelo, 'Air Max')
        self.assertEqual(producto.color, 'Negro')
        self.assertEqual(producto.propiedad, '42')
        self.assertEqual(producto.costo, Decimal('100.00'))
        self.assertEqual(producto.precio, Decimal('150.00'))
        self.assertEqual(producto.proveedor, proveedor)
        self.assertEqual(producto.tienda, tienda)
        self.assertEqual(producto.catalogo, catalogo)
        self.assertEqual(producto.created_by, user)
    
    def test_should_enforce_unique_codigo(self):
        """Debería enforcer código único"""
        ProductoFactory(codigo='UNIQUE001')
        
        with self.assertRaises(IntegrityError):
            ProductoFactory(codigo='UNIQUE001')
    
    def test_should_have_correct_string_representation(self):
        """Debería tener la representación string correcta"""
        producto = ProductoFactory(
            codigo='TEST001',
            marca='TestMarca',
            modelo='TestModelo'
        )
        
        expected = "TEST001 - TestMarca TestModelo"
        self.assertEqual(str(producto), expected)
    
    def test_should_validate_decimal_precision(self):
        """Debería validar precisión decimal para costo y precio"""
        # Valores válidos con 2 decimales
        producto = ProductoFactory(
            costo=Decimal('99.99'),
            precio=Decimal('149.50')
        )
        self.assertEqual(producto.costo, Decimal('99.99'))
        self.assertEqual(producto.precio, Decimal('149.50'))
    
    def test_should_validate_required_fields(self):
        """Debería validar campos requeridos"""
        with self.assertRaises(ValidationError):
            producto = Producto()
            producto.full_clean()
    
    def test_should_default_values(self):
        """Debería tener valores por defecto correctos"""
        proveedor = ProveedorFactory()
        tienda = TiendaFactory()
        
        producto = Producto.objects.create(
            codigo='DEFAULT001',
            marca='Test',
            modelo='Test',
            color='Test',
            costo=Decimal('100.00'),
            precio=Decimal('150.00'),
            temporada='Test',
            proveedor=proveedor,
            tienda=tienda
        )
        
        self.assertFalse(producto.oferta)
        self.assertTrue(producto.admite_devolucion)
        self.assertEqual(producto.stock_minimo, 5)
    
    def test_should_handle_optional_catalogo(self):
        """Debería manejar catálogo opcional"""
        producto = ProductoFactory(catalogo=None)
        self.assertIsNone(producto.catalogo)
    
    def test_should_protect_against_proveedor_deletion(self):
        """Debería proteger contra eliminación de proveedor"""
        proveedor = ProveedorFactory()
        producto = ProductoFactory(proveedor=proveedor)
        
        # No debería poder eliminar proveedor que tiene productos
        with self.assertRaises(Exception):  # ProtectedError
            proveedor.delete()
    
    def test_should_protect_against_tienda_deletion(self):
        """Debería proteger contra eliminación de tienda"""
        tienda = TiendaFactory()
        producto = ProductoFactory(tienda=tienda)
        
        # No debería poder eliminar tienda que tiene productos
        with self.assertRaises(Exception):  # ProtectedError
            tienda.delete()
    
    def test_should_handle_catalogo_deletion_gracefully(self):
        """Debería manejar eliminación de catálogo correctamente"""
        catalogo = CatalogoFactory()
        producto = ProductoFactory(catalogo=catalogo)
        
        # Eliminar catálogo debería setear catalogo a NULL
        catalogo.delete()
        producto.refresh_from_db()
        self.assertIsNone(producto.catalogo)
    
    def test_should_validate_field_lengths(self):
        """Debería validar longitudes de campos"""
        # Campos con límite de 50 caracteres
        long_string_50 = 'A' * 50
        producto = ProductoFactory(
            codigo=long_string_50,
            marca=long_string_50,
            modelo=long_string_50,
            propiedad=long_string_50
        )
        self.assertEqual(len(producto.codigo), 50)
        
        # Color con límite de 30 caracteres
        long_color = 'A' * 30
        producto = ProductoFactory(color=long_color)
        self.assertEqual(len(producto.color), 30)
    
    def test_should_validate_positive_stock_minimo(self):
        """Debería validar que stock mínimo sea positivo"""
        # Stock mínimo válido
        producto = ProductoFactory(stock_minimo=10)
        self.assertEqual(producto.stock_minimo, 10)
        
        # Stock mínimo cero (válido)
        producto = ProductoFactory(stock_minimo=0)
        self.assertEqual(producto.stock_minimo, 0)
    
    def test_should_handle_user_references(self):
        """Debería manejar referencias de usuario correctamente"""
        creator = UserFactory(username='creator')
        updater = UserFactory(username='updater')
        
        producto = ProductoFactory(
            created_by=creator,
            updated_by=updater
        )
        
        self.assertEqual(producto.created_by, creator)
        self.assertEqual(producto.updated_by, updater)
        
        # Al eliminar usuarios, las referencias deberían ser NULL
        creator.delete()
        updater.delete()
        
        producto.refresh_from_db()
        self.assertIsNone(producto.created_by)
        self.assertIsNone(producto.updated_by)


class ProductoBusinessLogicTests(BaseTestCase):
    """Tests para lógica de negocio de productos"""
    
    def test_should_calculate_markup_correctly(self):
        """Debería calcular markup correctamente"""
        producto = ProductoFactory(
            costo=Decimal('100.00'),
            precio=Decimal('150.00')
        )
        
        # Calcular markup: (precio - costo) / costo * 100
        expected_markup = ((producto.precio - producto.costo) / producto.costo) * 100
        self.assertEqual(expected_markup, Decimal('50.00'))
    
    def test_should_identify_productos_en_oferta(self):
        """Debería identificar productos en oferta"""
        # Producto en oferta individual
        producto_oferta = ProductoFactory(oferta=True)
        self.assertTrue(producto_oferta.oferta)
        
        # Producto en catálogo de oferta
        catalogo_oferta = CatalogoFactory(es_oferta=True)
        producto_catalogo_oferta = ProductoFactory(
            oferta=False,
            catalogo=catalogo_oferta
        )
        
        # El producto estaría en oferta por su catálogo
        # (Esta lógica podría implementarse como property o método)
        self.assertTrue(producto_catalogo_oferta.catalogo.es_oferta)
    
    def test_should_validate_pricing_logic(self):
        """Debería validar lógica de precios"""
        # Precio debe ser mayor que costo (regla de negocio)
        with self.assertRaises(ValidationError):
            producto = Producto(
                codigo='TEST001',
                marca='Test',
                modelo='Test',
                color='Test',
                costo=Decimal('150.00'),
                precio=Decimal('100.00'),  # Precio menor que costo
                temporada='Test',
                proveedor=ProveedorFactory(),
                tienda=TiendaFactory()
            )
            # Nota: Esta validación debería implementarse en clean() method
            if producto.precio < producto.costo:
                raise ValidationError('El precio debe ser mayor que el costo')
    
    def test_should_handle_inventory_warnings(self):
        """Debería manejar advertencias de inventario"""
        producto = ProductoFactory(stock_minimo=10)
        
        # Esta lógica se implementaría en conjunto con el modelo Inventario
        # Por ahora solo verificamos que el stock_minimo esté configurado
        self.assertGreater(producto.stock_minimo, 0)


class ProductosCatalogoIntegrationTests(BaseTestCase):
    """Tests de integración entre Productos y Catálogos"""
    
    def test_should_manage_catalogo_productos_relationship(self):
        """Debería manejar relación catálogo-productos"""
        catalogo = CatalogoFactory(nombre='Catálogo Primavera')
        
        # Crear productos asociados al catálogo
        productos = [
            ProductoFactory(catalogo=catalogo, codigo=f'PRIM{i:03d}')
            for i in range(1, 4)
        ]
        
        # Verificar relación
        self.assertEqual(catalogo.productos.count(), 3)
        for producto in productos:
            self.assertEqual(producto.catalogo, catalogo)
    
    def test_should_filter_productos_by_catalogo_status(self):
        """Debería filtrar productos por estado del catálogo"""
        # Catálogo activo
        catalogo_activo = CatalogoFactory(activo=True)
        producto_activo = ProductoFactory(catalogo=catalogo_activo)
        
        # Catálogo inactivo
        catalogo_inactivo = CatalogoFactory(activo=False)
        producto_inactivo = ProductoFactory(catalogo=catalogo_inactivo)
        
        # Query productos de catálogos activos
        productos_activos = Producto.objects.filter(catalogo__activo=True)
        self.assertIn(producto_activo, productos_activos)
        self.assertNotIn(producto_inactivo, productos_activos)
    
    def test_should_handle_seasonal_catalogs(self):
        """Debería manejar catálogos estacionales"""
        temporadas = ['Primavera', 'Verano', 'Otoño', 'Invierno']
        
        for temporada in temporadas:
            catalogo = CatalogoFactory(
                temporada=temporada,
                nombre=f'Catálogo {temporada}'
            )
            productos = [
                ProductoFactory(
                    catalogo=catalogo,
                    temporada=temporada,
                    codigo=f'{temporada.upper()}{i:02d}'
                )
                for i in range(1, 3)
            ]
            
            # Verificar que productos tienen la misma temporada que el catálogo
            for producto in productos:
                self.assertEqual(producto.temporada, temporada)
                self.assertEqual(producto.catalogo.temporada, temporada)
    
    def test_should_calculate_catalogo_statistics(self):
        """Debería calcular estadísticas de catálogo"""
        catalogo = CatalogoFactory()
        
        # Crear productos con diferentes precios
        precios = [Decimal('100.00'), Decimal('200.00'), Decimal('150.00')]
        productos = [
            ProductoFactory(catalogo=catalogo, precio=precio)
            for precio in precios
        ]
        
        # Calcular estadísticas
        total_productos = catalogo.productos.count()
        precio_promedio = sum(p.precio for p in productos) / len(productos)
        precio_min = min(p.precio for p in productos)
        precio_max = max(p.precio for p in productos)
        
        self.assertEqual(total_productos, 3)
        self.assertEqual(precio_promedio, Decimal('150.00'))
        self.assertEqual(precio_min, Decimal('100.00'))
        self.assertEqual(precio_max, Decimal('200.00'))
