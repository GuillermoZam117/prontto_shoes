# filepath: c:\catalog_pos\productos\tests\test_htmx_productos.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from productos.models import Producto, Catalogo
from proveedores.models import Proveedor
from tiendas.models import Tienda
from decimal import Decimal


class ProductoHTMXTestCase(TestCase):
    """Test cases específicos para funcionalidad HTMX en productos"""
    
    def setUp(self):
        """Set up test data for HTMX tests"""
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass')
          # Create test tienda
        self.tienda = Tienda.objects.create(
            nombre='Tienda Test HTMX',
            direccion='Test Address',
            contacto='123456789'
        )
        
        # Create test proveedor
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Test HTMX',
            contacto='test@proveedor.com',
            requiere_anticipo=False,
            max_return_days=30
        )
        
        # Create test catalogo
        self.catalogo1 = Catalogo.objects.create(
            nombre='Catálogo Primavera 2025',
            temporada='Primavera',
            es_oferta=False,
            activo=True
        )
        
        self.catalogo2 = Catalogo.objects.create(
            nombre='Catálogo Ofertas',
            temporada='Verano',
            es_oferta=True,
            activo=True
        )
        
        # Create test productos
        self.producto1 = Producto.objects.create(
            codigo='PROD001',
            marca='Nike',
            modelo='Air Max 90',
            color='Blanco',
            propiedad='Talla 9',
            costo=Decimal('50.00'),
            precio=Decimal('120.00'),
            temporada='Primavera',
            oferta=False,
            admite_devolucion=True,
            stock_minimo=10,
            proveedor=self.proveedor,
            tienda=self.tienda,
            catalogo=self.catalogo1,
            created_by=self.user
        )
        
        self.producto2 = Producto.objects.create(
            codigo='PROD002',
            marca='Adidas',
            modelo='Stan Smith',
            color='Verde',
            propiedad='Talla 8',
            costo=Decimal('40.00'),
            precio=Decimal('100.00'),
            temporada='Verano',
            oferta=True,
            admite_devolucion=True,
            stock_minimo=5,
            proveedor=self.proveedor,
            tienda=self.tienda,
            catalogo=self.catalogo2,
            created_by=self.user
        )
        
        self.producto3 = Producto.objects.create(
            codigo='SEARCH123',
            marca='Converse',
            modelo='Chuck Taylor',
            color='Negro',
            propiedad='Talla 10',
            costo=Decimal('30.00'),
            precio=Decimal('80.00'),
            temporada='Otoño',
            oferta=False,
            admite_devolucion=False,
            stock_minimo=8,
            proveedor=self.proveedor,
            tienda=self.tienda,
            catalogo=self.catalogo1,
            created_by=self.user
        )
        
    def test_producto_list_htmx_search(self):
        """Test HTMX search functionality"""
        response = self.client.get(
            reverse('productos:lista'),
            {'q': 'Nike'},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nike')
        self.assertContains(response, 'Air Max 90')
        self.assertNotContains(response, 'Adidas')
        self.assertNotContains(response, 'Converse')
        
        # Verify HTMX template is used (partial)
        self.assertTemplateUsed(response, 'productos/partials/producto_table.html')
        
    def test_producto_list_htmx_search_by_codigo(self):
        """Test HTMX search by código functionality"""
        response = self.client.get(
            reverse('productos:lista'),
            {'q': 'PROD001'},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PROD001')
        self.assertContains(response, 'Nike')
        self.assertNotContains(response, 'PROD002')
        self.assertNotContains(response, 'SEARCH123')
        
    def test_producto_list_htmx_search_by_modelo(self):
        """Test HTMX search by modelo functionality"""
        response = self.client.get(
            reverse('productos:lista'),
            {'q': 'Stan Smith'},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Stan Smith')
        self.assertContains(response, 'Adidas')
        self.assertNotContains(response, 'Nike')
        self.assertNotContains(response, 'Converse')
        
    def test_producto_list_htmx_search_by_color(self):
        """Test HTMX search by color functionality"""
        response = self.client.get(
            reverse('productos:lista'),
            {'q': 'Negro'},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Negro')
        self.assertContains(response, 'Converse')
        self.assertNotContains(response, 'Nike')
        self.assertNotContains(response, 'Adidas')
        
    def test_producto_list_htmx_filter_by_temporada(self):
        """Test HTMX filtering by temporada"""
        response = self.client.get(
            reverse('productos:lista'),
            {'temporada': 'Primavera'},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nike')
        self.assertNotContains(response, 'Adidas')
        self.assertNotContains(response, 'Converse')
        
    def test_producto_list_htmx_filter_by_oferta_true(self):
        """Test HTMX filtering by oferta=true"""
        response = self.client.get(
            reverse('productos:lista'),
            {'oferta': 'true'},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Adidas')
        self.assertContains(response, 'Stan Smith')
        self.assertNotContains(response, 'Nike')
        self.assertNotContains(response, 'Converse')
        
    def test_producto_list_htmx_filter_by_oferta_false(self):
        """Test HTMX filtering by oferta=false"""
        response = self.client.get(
            reverse('productos:lista'),
            {'oferta': 'false'},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nike')
        self.assertContains(response, 'Converse')
        self.assertNotContains(response, 'Adidas')
        
    def test_producto_list_htmx_filter_by_catalogo(self):
        """Test HTMX filtering by catalogo"""
        response = self.client.get(
            reverse('productos:lista'),
            {'catalogo': self.catalogo2.id},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Adidas')
        self.assertNotContains(response, 'Nike')
        self.assertNotContains(response, 'Converse')
        
    def test_producto_list_htmx_filter_by_precio_range(self):
        """Test HTMX filtering by precio range"""
        response = self.client.get(
            reverse('productos:lista'),
            {'precio_min': '90', 'precio_max': '110'},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Adidas')  # $100
        self.assertNotContains(response, 'Nike')  # $120
        self.assertNotContains(response, 'Converse')  # $80
        
    def test_producto_list_htmx_combined_filters(self):
        """Test HTMX with combined search and filter"""
        response = self.client.get(
            reverse('productos:lista'),
            {'q': 'Adidas', 'oferta': 'true'},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Adidas')
        self.assertContains(response, 'Stan Smith')
        self.assertNotContains(response, 'Nike')
        self.assertNotContains(response, 'Converse')
        
    def test_producto_list_htmx_empty_search(self):
        """Test HTMX with empty search returns all"""
        response = self.client.get(
            reverse('productos:lista'),
            {'q': ''},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nike')
        self.assertContains(response, 'Adidas')
        self.assertContains(response, 'Converse')
        
    def test_producto_list_htmx_no_results(self):
        """Test HTMX search with no results"""
        response = self.client.get(
            reverse('productos:lista'),
            {'q': 'NoExiste'},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        # Check for empty state message
        self.assertContains(response, 'No hay productos para mostrar')
        
    def test_producto_list_htmx_headers(self):
        """Test that HTMX request returns correct headers"""
        response = self.client.get(
            reverse('productos:lista'),
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        # Verify it's treated as HTMX request by checking template used
        self.assertTemplateUsed(response, 'productos/partials/producto_table.html')
        
    def test_producto_list_non_htmx_request(self):
        """Test that non-HTMX request returns full page"""
        response = self.client.get(reverse('productos:lista'))
        
        self.assertEqual(response.status_code, 200)
        # Should use full template, not partial
        self.assertTemplateUsed(response, 'productos/producto_list.html')
        
    def test_producto_search_case_insensitive(self):
        """Test HTMX search is case insensitive"""
        response = self.client.get(
            reverse('productos:lista'),
            {'q': 'nike'},  # lowercase
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nike')
        self.assertContains(response, 'Air Max 90')
        
    def test_producto_search_partial_match(self):
        """Test HTMX search with partial matches"""
        response = self.client.get(
            reverse('productos:lista'),
            {'q': 'Max'},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Air Max 90')
        self.assertNotContains(response, 'Stan Smith')
        
    def test_producto_detail_htmx(self):
        """Test HTMX detail view functionality"""
        detail_url = reverse('productos:detalle', kwargs={'pk': self.producto1.pk})
        
        response = self.client.get(detail_url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'productos/producto_detail.html')
        self.assertContains(response, 'Nike')
        self.assertContains(response, 'Air Max 90')
        self.assertContains(response, 'PROD001')
        
    def test_producto_create_htmx(self):
        """Test HTMX create functionality"""
        create_url = reverse('productos:nuevo')
        
        # Test GET request for form
        response = self.client.get(create_url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'productos/producto_form.html')
        
        # Test POST request to create
        producto_data = {
            'codigo': 'NEWPROD001',
            'marca': 'Nuevo Producto HTMX',
            'modelo': 'Test Model',
            'color': 'Azul',
            'propiedad': 'Talla 11',
            'costo': '35.00',
            'precio': '90.00',
            'temporada': 'Invierno',
            'oferta': False,
            'admite_devolucion': True,
            'stock_minimo': 5,
            'proveedor': self.proveedor.id,
            'tienda': self.tienda.id,
            'catalogo': self.catalogo1.id
        }
        
        response = self.client.post(
            create_url,
            producto_data,
            HTTP_HX_REQUEST='true'
        )
        
        # Should redirect or return success response
        self.assertIn(response.status_code, [200, 201, 302])
        
        # Verify product was created
        self.assertTrue(
            Producto.objects.filter(codigo='NEWPROD001').exists()
        )
        
    def test_producto_edit_htmx(self):
        """Test HTMX edit functionality"""
        edit_url = reverse('productos:editar', kwargs={'pk': self.producto1.pk})
        
        # Test GET request for form
        response = self.client.get(edit_url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'productos/producto_form.html')
        self.assertContains(response, 'Nike')
        
        # Test POST request to update
        updated_data = {
            'codigo': 'PROD001',
            'marca': 'Nike',
            'modelo': 'Air Max 90 Updated',
            'color': 'Blanco',
            'propiedad': 'Talla 9',
            'costo': '55.00',
            'precio': '130.00',
            'temporada': 'Primavera',
            'oferta': False,
            'admite_devolucion': True,
            'stock_minimo': 10,
            'proveedor': self.proveedor.id,
            'tienda': self.tienda.id,
            'catalogo': self.catalogo1.id
        }
        
        response = self.client.post(
            edit_url,
            updated_data,
            HTTP_HX_REQUEST='true'
        )
        
        # Should redirect or return success response
        self.assertIn(response.status_code, [200, 201, 302])
        
        # Verify product was updated
        updated_producto = Producto.objects.get(pk=self.producto1.pk)
        self.assertEqual(updated_producto.modelo, 'Air Max 90 Updated')
        self.assertEqual(str(updated_producto.precio), '130.00')
        
    def test_producto_delete_htmx(self):
        """Test HTMX delete functionality"""
        delete_url = reverse('productos:eliminar', kwargs={'pk': self.producto3.pk})
        
        # Test POST request to delete
        response = self.client.post(delete_url, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertIn('eliminado exitosamente', response_data['message'])
        
        # Verify product was deleted
        self.assertFalse(
            Producto.objects.filter(pk=self.producto3.pk).exists()
        )
        
    def test_producto_invalid_delete_htmx(self):
        """Test HTMX delete with invalid product ID"""
        delete_url = reverse('productos:eliminar', kwargs={'pk': 99999})
        
        response = self.client.post(delete_url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 404)
        
    def test_producto_multiple_filters_htmx(self):
        """Test HTMX with multiple filter combinations"""
        response = self.client.get(
            reverse('productos:lista'),
            {
                'q': 'Nike',
                'temporada': 'Primavera',
                'oferta': 'false',
                'precio_min': '100'
            },
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nike')
        self.assertContains(response, 'Air Max 90')
        self.assertNotContains(response, 'Adidas')
        self.assertNotContains(response, 'Converse')
        
    def test_producto_pagination_htmx(self):
        """Test HTMX pagination functionality"""
        # Create more products to test pagination
        for i in range(15):
            Producto.objects.create(
                codigo=f'PAGPROD{i:03d}',
                marca=f'Marca Pagination {i}',
                modelo=f'Modelo {i}',
                color='Test Color',
                propiedad=f'Talla {i}',
                costo=Decimal('30.00'),
                precio=Decimal('70.00'),
                temporada='Test',
                oferta=(i % 2 == 0),
                admite_devolucion=True,
                stock_minimo=5,
                proveedor=self.proveedor,
                tienda=self.tienda,
                catalogo=self.catalogo1,
                created_by=self.user
            )
        
        response = self.client.get(
            reverse('productos:lista'),
            {'page': 2},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'productos/partials/producto_table.html')
