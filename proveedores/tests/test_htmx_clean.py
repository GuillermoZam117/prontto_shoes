from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from proveedores.models import Proveedor


class ProveedorHTMXTestCase(TestCase):
    """Test cases específicos para funcionalidad HTMX en proveedores"""
    
    def setUp(self):
        """Set up test data for HTMX tests"""
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass')
        
        # Crear proveedores de prueba con campos correctos del modelo
        self.proveedor1 = Proveedor.objects.create(
            nombre='Proveedor HTMX 1',
            contacto='proveedor1@htmx.com',
            requiere_anticipo=True,
            max_return_days=30
        )
        self.proveedor2 = Proveedor.objects.create(
            nombre='Proveedor HTMX 2',
            contacto='proveedor2@htmx.com',
            requiere_anticipo=False,
            max_return_days=15
        )
        self.proveedor3 = Proveedor.objects.create(
            nombre='Test Search Proveedor',
            contacto='test@search.com',
            requiere_anticipo=True,
            max_return_days=0
        )
        
    def test_proveedor_list_htmx_search(self):
        """Test HTMX search functionality"""
        response = self.client.get(
            reverse('proveedores:lista'),
            {'q': 'HTMX'},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Proveedor HTMX 1')
        self.assertContains(response, 'Proveedor HTMX 2')
        self.assertNotContains(response, 'Test Search Proveedor')
        
        # Verify HTMX template is used (partial)
        self.assertTemplateUsed(response, 'proveedores/partials/proveedor_table.html')
    
    def test_proveedor_list_htmx_filter_by_requiere_anticipo_true(self):
        """Test HTMX filtering by requiere_anticipo=true"""
        response = self.client.get(
            reverse('proveedores:lista'),
            {'requiere_anticipo': 'true'},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Proveedor HTMX 1')
        self.assertContains(response, 'Test Search Proveedor')
        self.assertNotContains(response, 'Proveedor HTMX 2')
    
    def test_proveedor_list_htmx_filter_by_requiere_anticipo_false(self):
        """Test HTMX filtering by requiere_anticipo=false"""
        response = self.client.get(
            reverse('proveedores:lista'),
            {'requiere_anticipo': 'false'},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Proveedor HTMX 2')
        self.assertNotContains(response, 'Proveedor HTMX 1')
        self.assertNotContains(response, 'Test Search Proveedor')
    
    def test_proveedor_list_htmx_combined_filters(self):
        """Test HTMX with combined search and filter"""
        response = self.client.get(
            reverse('proveedores:lista'),
            {'q': 'Test', 'requiere_anticipo': 'true'},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Search Proveedor')
        self.assertNotContains(response, 'Proveedor HTMX 1')
        self.assertNotContains(response, 'Proveedor HTMX 2')
    
    def test_proveedor_list_htmx_empty_search(self):
        """Test HTMX with empty search returns all"""
        response = self.client.get(
            reverse('proveedores:lista'),
            {'q': ''},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Proveedor HTMX 1')
        self.assertContains(response, 'Proveedor HTMX 2')
        self.assertContains(response, 'Test Search Proveedor')
    
    def test_proveedor_list_htmx_no_results(self):
        """Test HTMX search with no results"""
        response = self.client.get(
            reverse('proveedores:lista'),
            {'q': 'NoExiste'},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        # Check for empty state message
        self.assertContains(response, 'No hay proveedores para mostrar')
    
    def test_proveedor_list_htmx_headers(self):
        """Test that HTMX request returns correct headers"""
        response = self.client.get(
            reverse('proveedores:lista'),
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        # Verify it's treated as HTMX request by checking template used
        self.assertTemplateUsed(response, 'proveedores/partials/proveedor_table.html')
    
    def test_proveedor_list_non_htmx_request(self):
        """Test that non-HTMX request returns full page"""
        response = self.client.get(reverse('proveedores:lista'))
        
        self.assertEqual(response.status_code, 200)
        # Should use full template, not partial
        self.assertTemplateUsed(response, 'proveedores/proveedor_list.html')
    
    def test_proveedor_search_by_contacto(self):
        """Test HTMX search by contacto functionality"""
        response = self.client.get(
            reverse('proveedores:lista'),
            {'q': 'proveedor1@htmx.com'},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Proveedor HTMX 1')
        self.assertNotContains(response, 'Proveedor HTMX 2')
        self.assertNotContains(response, 'Test Search Proveedor')
    
    def test_proveedor_delete_htmx(self):
        """Test HTMX delete functionality"""
        # Create a provider that can be safely deleted
        test_proveedor = Proveedor.objects.create(
            nombre='Proveedor Para Eliminar',
            contacto='eliminar@test.com',
            requiere_anticipo=False,
            max_return_days=7
        )
        
        delete_url = reverse('proveedores:eliminar', kwargs={'pk': test_proveedor.pk})
        response = self.client.post(
            delete_url,
            HTTP_HX_REQUEST='true'
        )
        
        # Should return success JsonResponse
        self.assertEqual(response.status_code, 200)
        
        # Check JSON response
        json_response = response.json()
        self.assertTrue(json_response['success'])
        
        # Verify provider was deleted
        with self.assertRaises(Proveedor.DoesNotExist):
            Proveedor.objects.get(pk=test_proveedor.pk)
    
    def test_proveedor_filter_by_max_return_days(self):
        """Test HTMX filtering by max_return_days range"""
        response = self.client.get(
            reverse('proveedores:lista'),
            {'max_return_days_min': '20'},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Proveedor HTMX 1')  # has 30 days
        self.assertNotContains(response, 'Proveedor HTMX 2')  # has 15 days
        self.assertNotContains(response, 'Test Search Proveedor')  # has 0 days
    
    def test_proveedor_create_htmx(self):
        """Test HTMX create functionality"""
        create_url = reverse('proveedores:nuevo')
        
        # Test GET request for form
        response = self.client.get(create_url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'proveedores/proveedor_form.html')
        
        # Test POST request to create
        proveedor_data = {
            'nombre': 'Nuevo Proveedor HTMX',
            'contacto': 'nuevo@htmx.com',
            'requiere_anticipo': 'on',  # HTML checkbox value
            'max_return_days': 45
        }
        
        response = self.client.post(
            create_url,
            proveedor_data,
            HTTP_HX_REQUEST='true'
        )
        
        # Should redirect or return success response
        self.assertIn(response.status_code, [200, 201, 302])
        
        # Verify provider was created
        self.assertTrue(
            Proveedor.objects.filter(nombre='Nuevo Proveedor HTMX').exists()
        )
    
    def test_proveedor_edit_htmx(self):
        """Test HTMX edit functionality"""
        edit_url = reverse('proveedores:editar', kwargs={'pk': self.proveedor1.pk})
        
        # Test GET request for form
        response = self.client.get(edit_url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'proveedores/proveedor_form.html')
        
        # Test POST request to update
        updated_data = {
            'nombre': 'Proveedor HTMX 1 Actualizado',
            'contacto': 'actualizado@htmx.com',
            'max_return_days': 60
        }
        
        response = self.client.post(
            edit_url,
            updated_data,
            HTTP_HX_REQUEST='true'
        )
        
        # Should redirect or return success response
        self.assertIn(response.status_code, [200, 302])
        
        # Verify provider was updated
        updated_proveedor = Proveedor.objects.get(pk=self.proveedor1.pk)
        self.assertEqual(updated_proveedor.nombre, 'Proveedor HTMX 1 Actualizado')
        self.assertEqual(updated_proveedor.contacto, 'actualizado@htmx.com')
        self.assertEqual(updated_proveedor.max_return_days, 60)
    
    def test_proveedor_detail_htmx(self):
        """Test HTMX detail view functionality"""
        detail_url = reverse('proveedores:detalle', kwargs={'pk': self.proveedor1.pk})
        
        response = self.client.get(detail_url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'proveedores/proveedor_detail.html')
        self.assertContains(response, 'Proveedor HTMX 1')
        self.assertContains(response, 'proveedor1@htmx.com')
    
    def test_proveedor_search_case_insensitive(self):
        """Test HTMX search is case insensitive"""
        response = self.client.get(
            reverse('proveedores:lista'),
            {'q': 'htmx'},  # lowercase
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Proveedor HTMX 1')
        self.assertContains(response, 'Proveedor HTMX 2')
    
    def test_proveedor_search_partial_match(self):
        """Test HTMX search with partial matches"""
        response = self.client.get(
            reverse('proveedores:lista'),
            {'q': 'Search'},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Search Proveedor')
        self.assertNotContains(response, 'Proveedor HTMX 1')
        self.assertNotContains(response, 'Proveedor HTMX 2')
    
    def test_proveedor_invalid_delete_htmx(self):
        """Test HTMX delete with invalid provider ID"""
        delete_url = reverse('proveedores:eliminar', kwargs={'pk': 99999})
        
        response = self.client.post(delete_url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 404)
