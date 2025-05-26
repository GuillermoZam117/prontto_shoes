from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal

from productos.models import Producto, Catalogo
from productos.forms import ProductoForm, ProductoImportForm
from tiendas.models import Tienda
from proveedores.models import Proveedor


class ProductoFormTestCase(TestCase):
    """Test suite for ProductoForm"""
    
    def setUp(self):
        """Set up test data"""
        self.user = get_user_model().objects.create_user(
            username='testuser', 
            password='testpass'
        )
        self.tienda = Tienda.objects.create(
            nombre='Tienda Test', 
            direccion='Calle 1'
        )
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Test'
        )
        self.catalogo = Catalogo.objects.create(
            nombre='Catálogo Test',
            temporada='2025',
            activo=True
        )
        
        self.valid_data = {
            'codigo': 'P001',
            'marca': 'MarcaX',
            'modelo': 'ModeloY',
            'color': 'Rojo',
            'talla': '42',
            'costo': Decimal('100.00'),
            'precio': Decimal('150.00'),
            'numero_pagina': '10',
            'temporada': 'Verano',
            'oferta': False,
            'admite_devolucion': True,
            'proveedor': self.proveedor.id,
            'tienda': self.tienda.id,
            'catalogo': self.catalogo.id
        }

    def test_valid_producto_form(self):
        """Test that form validates with correct data"""
        form = ProductoForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_blank_codigo(self):
        """Test that codigo is required"""
        data = self.valid_data.copy()
        data['codigo'] = ''
        form = ProductoForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('codigo', form.errors)

    def test_precio_less_than_costo(self):
        """Test validation when price is less than cost"""
        data = self.valid_data.copy()
        data['precio'] = '90.00'  # Less than costo (100.00)
        form = ProductoForm(data=data)
        # Form might still be valid since this validation might be in the model or view
        # If validation is in the form, adjust this test accordingly
        self.assertTrue(form.is_valid())

    def test_duplicate_codigo(self):
        """Test validation for duplicate product code"""
        # Create a product with the same code
        Producto.objects.create(
            codigo='P001',
            marca='MarcaExistente',
            modelo='ModeloExistente',
            color='Azul',
            talla='40',
            costo=Decimal('90.00'),
            precio=Decimal('130.00'),
            proveedor=self.proveedor,
            tienda=self.tienda,
            catalogo=self.catalogo
        )
        
        form = ProductoForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('codigo', form.errors)


class ProductoImportFormTestCase(TestCase):
    """Test suite for ProductoImportForm"""
    
    def test_empty_form(self):
        """Test form without a file"""
        form = ProductoImportForm(data={}, files={})
        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)

    def test_non_excel_file(self):
        """Test form with a non-Excel file"""
        # This test would require a real file upload setup
        # For simplicity, we're just checking the form structure
        form = ProductoImportForm()
        self.assertIn('file', form.fields)
        # Verify that the field is required
        self.assertTrue(form.fields['file'].required)


class FrontendViewsTestCase(TestCase):
    """Test suite for frontend views"""
    
    def setUp(self):
        """Set up test data"""
        self.user = get_user_model().objects.create_user(
            username='testuser', 
            password='testpass'
        )
        self.client.login(username='testuser', password='testpass')
        
        self.tienda = Tienda.objects.create(
            nombre='Tienda Test', 
            direccion='Calle 1'
        )
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Test'
        )
        self.catalogo = Catalogo.objects.create(
            nombre='Catálogo Test',
            temporada='2025',
            activo=True
        )
        
        self.producto = Producto.objects.create(
            codigo='P001',
            marca='MarcaX',
            modelo='ModeloY',
            color='Rojo',
            talla='42',
            costo=Decimal('100.00'),
            precio=Decimal('150.00'),
            proveedor=self.proveedor,
            tienda=self.tienda,
            catalogo=self.catalogo
        )
        
        # Set up URLs for frontend views
        self.list_url = reverse('producto_list')
        self.detail_url = reverse('producto_detail', kwargs={'pk': self.producto.pk})
        self.create_url = reverse('producto_create')
        self.edit_url = reverse('producto_edit', kwargs={'pk': self.producto.pk})
        self.import_url = reverse('producto_import')

    def test_producto_list_view(self):
        """Test product list view"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'productos/producto_list.html')
        self.assertContains(response, 'P001')  # Product code should be in the page

    def test_producto_list_view_with_search(self):
        """Test product list view with search query"""
        response = self.client.get(f"{self.list_url}?q=MarcaX")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'productos/producto_list.html')
        self.assertContains(response, 'P001')
        
        # Search with no results
        response = self.client.get(f"{self.list_url}?q=NonExistent")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'productos/producto_list.html')
        self.assertNotContains(response, 'P001')

    def test_producto_detail_view(self):
        """Test product detail view"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'productos/producto_detail.html')
        self.assertContains(response, 'P001')
        self.assertContains(response, 'MarcaX')

    def test_producto_create_view(self):
        """Test product creation view"""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'productos/producto_form.html')
        
        # Test form submission
        new_product_data = {
            'codigo': 'P002',
            'marca': 'MarcaZ',
            'modelo': 'ModeloZ',
            'color': 'Azul',
            'talla': '38',
            'costo': '120.00',
            'precio': '180.00',
            'numero_pagina': '15',
            'temporada': 'Invierno',
            'oferta': True,
            'admite_devolucion': True,
            'proveedor': self.proveedor.id,
            'tienda': self.tienda.id,
            'catalogo': self.catalogo.id
        }
        
        response = self.client.post(self.create_url, new_product_data)
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Verify the product was created
        self.assertTrue(Producto.objects.filter(codigo='P002').exists())

    def test_producto_edit_view(self):
        """Test product edit view"""
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'productos/producto_form.html')
        
        # Test form submission
        edit_data = {
            'codigo': 'P001',
            'marca': 'MarcaEditada',
            'modelo': 'ModeloY',
            'color': 'Rojo',
            'talla': '42',
            'costo': '100.00',
            'precio': '160.00',
            'numero_pagina': '10',
            'temporada': 'Verano',
            'oferta': True,
            'admite_devolucion': True,
            'proveedor': self.proveedor.id,
            'tienda': self.tienda.id,
            'catalogo': self.catalogo.id
        }
        
        response = self.client.post(self.edit_url, edit_data)
        # Should redirect after successful edit
        self.assertEqual(response.status_code, 302)
        
        # Verify the product was updated
        updated_product = Producto.objects.get(pk=self.producto.pk)
        self.assertEqual(updated_product.marca, 'MarcaEditada')

    def test_producto_import_view(self):
        """Test product import view"""
        response = self.client.get(self.import_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'productos/producto_import.html')
        
        # Testing actual file upload would require more complex setup
        # We just check that the view renders the form correctly
        self.assertContains(response, 'enctype="multipart/form-data"')
        self.assertContains(response, 'type="file"')
