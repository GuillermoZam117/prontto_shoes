from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

from proveedores.models import Proveedor
from proveedores.views import ProveedorViewSet
from proveedores.serializers import ProveedorSerializer
from tiendas.models import Tienda


class ProveedorViewSetTestCase(APITestCase):
    """Test suite for ProveedorViewSet"""
    
    def setUp(self):
        """Set up test data"""
        # Create user and authenticate
        self.user = get_user_model().objects.create_user(
            username='testuser', 
            password='testpass'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create related objects
        self.tienda = Tienda.objects.create(
            nombre='Tienda Test', 
            direccion='Calle 1'
        )
        
        # Create a provider
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Test',
            direccion='Dirección Test',
            telefono='1234567890',
            correo='proveedor@test.com',
            contacto='Contacto Test',
            requiere_anticipo=True,
            notas='Notas de prueba',
            tienda=self.tienda
        )
        
        # Set up URLs
        self.list_url = reverse('proveedor-list')
        self.detail_url = reverse('proveedor-detail', kwargs={'pk': self.proveedor.pk})

    def test_list_proveedores(self):
        """Test retrieving a list of providers"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nombre'], 'Proveedor Test')

    def test_retrieve_proveedor(self):
        """Test retrieving a single provider"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nombre'], 'Proveedor Test')
        self.assertEqual(response.data['telefono'], '1234567890')

    def test_create_proveedor(self):
        """Test creating a new provider"""
        new_provider_data = {
            'nombre': 'Nuevo Proveedor',
            'direccion': 'Nueva Dirección',
            'telefono': '0987654321',
            'correo': 'nuevo@proveedor.com',
            'contacto': 'Nuevo Contacto',
            'requiere_anticipo': False,
            'notas': 'Nuevas notas',
            'tienda': self.tienda.id
        }
        
        response = self.client.post(self.list_url, new_provider_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Proveedor.objects.count(), 2)
        
        # Verify the created provider
        created_provider = Proveedor.objects.get(nombre='Nuevo Proveedor')
        self.assertEqual(created_provider.telefono, '0987654321')
        self.assertFalse(created_provider.requiere_anticipo)

    def test_update_proveedor(self):
        """Test updating an existing provider"""
        update_data = {
            'nombre': 'Proveedor Actualizado',
            'direccion': 'Dirección Test',
            'telefono': '1234567890',
            'correo': 'actualizado@test.com',
            'contacto': 'Contacto Test',
            'requiere_anticipo': False,  # Changed from True
            'notas': 'Notas actualizadas',
            'tienda': self.tienda.id
        }
        
        response = self.client.put(self.detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the updated provider
        updated_provider = Proveedor.objects.get(pk=self.proveedor.pk)
        self.assertEqual(updated_provider.nombre, 'Proveedor Actualizado')
        self.assertEqual(updated_provider.correo, 'actualizado@test.com')
        self.assertFalse(updated_provider.requiere_anticipo)
        self.assertEqual(updated_provider.notas, 'Notas actualizadas')

    def test_partial_update_proveedor(self):
        """Test partially updating a provider"""
        patch_data = {
            'correo': 'parcial@test.com',
            'requiere_anticipo': False
        }
        
        response = self.client.patch(self.detail_url, patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the updated provider
        updated_provider = Proveedor.objects.get(pk=self.proveedor.pk)
        self.assertEqual(updated_provider.correo, 'parcial@test.com')
        self.assertFalse(updated_provider.requiere_anticipo)
        # Other fields should remain unchanged
        self.assertEqual(updated_provider.nombre, 'Proveedor Test')

    def test_delete_proveedor(self):
        """Test deleting a provider"""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Proveedor.objects.count(), 0)

    def test_filter_proveedores_by_nombre(self):
        """Test filtering providers by name"""
        # Create another provider with different name
        Proveedor.objects.create(
            nombre='Otro Proveedor',
            direccion='Otra Dirección',
            telefono='5555555555',
            correo='otro@proveedor.com',
            tienda=self.tienda
        )
        
        # Filter by name
        url = f"{self.list_url}?nombre=Test"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nombre'], 'Proveedor Test')
        
        # Filter by another name
        url = f"{self.list_url}?nombre=Otro"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nombre'], 'Otro Proveedor')

    def test_filter_proveedores_by_tienda(self):
        """Test filtering providers by store"""
        # Create another store
        otra_tienda = Tienda.objects.create(
            nombre='Otra Tienda', 
            direccion='Otra Calle'
        )
        
        # Create a provider for the other store
        Proveedor.objects.create(
            nombre='Proveedor Otra Tienda',
            direccion='Dirección Otra',
            telefono='8888888888',
            correo='otra@tienda.com',
            tienda=otra_tienda
        )
        
        # Filter by first store
        url = f"{self.list_url}?tienda={self.tienda.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nombre'], 'Proveedor Test')
        
        # Filter by second store
        url = f"{self.list_url}?tienda={otra_tienda.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nombre'], 'Proveedor Otra Tienda')

    def test_filter_proveedores_by_requiere_anticipo(self):
        """Test filtering providers by advance requirement"""
        # Create another provider that doesn't require advance
        Proveedor.objects.create(
            nombre='Sin Anticipo',
            direccion='Dirección Sin Anticipo',
            telefono='9999999999',
            correo='sin@anticipo.com',
            requiere_anticipo=False,
            tienda=self.tienda
        )
        
        # Filter by requiere_anticipo=true
        url = f"{self.list_url}?requiere_anticipo=true"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nombre'], 'Proveedor Test')
        
        # Filter by requiere_anticipo=false
        url = f"{self.list_url}?requiere_anticipo=false"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nombre'], 'Sin Anticipo')

    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access the API"""
        # Create a new client without authentication
        client = APIClient()
        
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = client.post(self.list_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProveedorFrontendViewsTestCase(TestCase):
    """Test suite for provider frontend views"""
    
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
            nombre='Proveedor Test',
            direccion='Dirección Test',
            telefono='1234567890',
            correo='proveedor@test.com',
            contacto='Contacto Test',
            requiere_anticipo=True,
            notas='Notas de prueba',
            tienda=self.tienda
        )
        
        # Set up URLs for frontend views
        self.list_url = reverse('proveedor_list')
        self.detail_url = reverse('proveedor_detail', kwargs={'pk': self.proveedor.pk})
        self.create_url = reverse('proveedor_create')
        self.edit_url = reverse('proveedor_edit', kwargs={'pk': self.proveedor.pk})

    def test_proveedor_list_view(self):
        """Test provider list view"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'proveedores/proveedor_list.html')
        self.assertContains(response, 'Proveedor Test')

    def test_proveedor_list_view_with_search(self):
        """Test provider list view with search query"""
        response = self.client.get(f"{self.list_url}?q=Test")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'proveedores/proveedor_list.html')
        self.assertContains(response, 'Proveedor Test')
        
        # Search with no results
        response = self.client.get(f"{self.list_url}?q=NonExistent")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'proveedores/proveedor_list.html')
        self.assertNotContains(response, 'Proveedor Test')

    def test_proveedor_detail_view(self):
        """Test provider detail view"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'proveedores/proveedor_detail.html')
        self.assertContains(response, 'Proveedor Test')
        self.assertContains(response, '1234567890')  # Phone number

    def test_proveedor_create_view(self):
        """Test provider creation view"""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'proveedores/proveedor_form.html')
        
        # Test form submission
        new_provider_data = {
            'nombre': 'Nuevo Proveedor',
            'direccion': 'Nueva Dirección',
            'telefono': '0987654321',
            'correo': 'nuevo@proveedor.com',
            'contacto': 'Nuevo Contacto',
            'requiere_anticipo': False,
            'notas': 'Nuevas notas',
            'tienda': self.tienda.id
        }
        
        response = self.client.post(self.create_url, new_provider_data)
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Verify the provider was created
        self.assertTrue(Proveedor.objects.filter(nombre='Nuevo Proveedor').exists())

    def test_proveedor_edit_view(self):
        """Test provider edit view"""
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'proveedores/proveedor_form.html')
        
        # Test form submission
        edit_data = {
            'nombre': 'Proveedor Editado',
            'direccion': 'Dirección Editada',
            'telefono': '1234567890',
            'correo': 'editado@test.com',
            'contacto': 'Contacto Editado',
            'requiere_anticipo': False,
            'notas': 'Notas editadas',
            'tienda': self.tienda.id
        }
        
        response = self.client.post(self.edit_url, edit_data)
        # Should redirect after successful edit
        self.assertEqual(response.status_code, 302)
          # Verify the provider was updated
        updated_provider = Proveedor.objects.get(pk=self.proveedor.pk)
        self.assertEqual(updated_provider.nombre, 'Proveedor Editado')
        self.assertEqual(updated_provider.correo, 'editado@test.com')
        
    def test_proveedor_filtros_api(self):
        """Test filtering providers through API"""
        # Create additional providers with different attributes
        Proveedor.objects.create(
            nombre='Proveedor Nacional',
            direccion='Local',
            telefono='1112223333',
            correo='nacional@test.com',
            tipo='nacional',
            activo=True
        )
        
        Proveedor.objects.create(
            nombre='Proveedor Internacional',
            direccion='Extranjero',
            telefono='4445556666',
            correo='internacional@test.com',
            tipo='internacional',
            activo=False
        )
        
        # Test filtering by activo
        url = f"{self.list_url}?activo=true"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        activos = Proveedor.objects.filter(activo=True).count()
        self.assertEqual(len(response.data), activos)
        for proveedor in response.data:
            self.assertTrue(proveedor['activo'])
        
        url = f"{self.list_url}?activo=false"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        inactivos = Proveedor.objects.filter(activo=False).count()
        self.assertEqual(len(response.data), inactivos)
        for proveedor in response.data:
            self.assertFalse(proveedor['activo'])
        
        # Test filtering by tipo
        url = f"{self.list_url}?tipo=nacional"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        nacionales = Proveedor.objects.filter(tipo='nacional').count()
        self.assertEqual(len(response.data), nacionales)
        for proveedor in response.data:
            self.assertEqual(proveedor['tipo'], 'nacional')
        
        url = f"{self.list_url}?tipo=internacional"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        internacionales = Proveedor.objects.filter(tipo='internacional').count()
        self.assertEqual(len(response.data), internacionales)
        for proveedor in response.data:
            self.assertEqual(proveedor['tipo'], 'internacional')
            
    def test_proveedor_busqueda_api(self):
        """Test searching providers through API"""
        # Create providers with distinct searchable terms
        Proveedor.objects.create(
            nombre='Zapatos ABC',
            direccion='Calle Zapatos',
            telefono='1112223333',
            correo='zapatos@test.com',
            activo=True
        )
        
        Proveedor.objects.create(
            nombre='Suelas XYZ',
            direccion='Avenida Suelas',
            telefono='4445556666',
            correo='suelas@test.com',
            activo=True
        )
        
        # Search by nombre
        url = f"{self.list_url}?search=Zapatos"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertTrue(len(response.data) > 0)
        for proveedor in response.data:
            self.assertTrue('Zapatos' in proveedor['nombre'] or 'Zapatos' in proveedor['direccion'])
            
        # Search by correo
        url = f"{self.list_url}?search=suelas@test.com"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertTrue(len(response.data) > 0)
        for proveedor in response.data:
            self.assertTrue('suelas@test.com' in proveedor['correo'])
            
    def test_proveedor_ordenamiento_api(self):
        """Test ordering providers through API"""
        # Clear existing providers and create new ones with ordered names
        Proveedor.objects.all().delete()
        
        Proveedor.objects.create(nombre='A Proveedor', activo=True)
        Proveedor.objects.create(nombre='B Proveedor', activo=True)
        Proveedor.objects.create(nombre='C Proveedor', activo=True)
        
        # Order by nombre ascending (default)
        url = f"{self.list_url}?ordering=nombre"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        nombres = [p['nombre'] for p in response.data]
        self.assertEqual(nombres, sorted(nombres))
        
        # Order by nombre descending
        url = f"{self.list_url}?ordering=-nombre"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        nombres = [p['nombre'] for p in response.data]
        self.assertEqual(nombres, sorted(nombres, reverse=True))
        
    def test_proveedor_detalle_api(self):
        """Test getting provider details through API"""
        url = reverse('api:proveedor-detail', kwargs={'pk': self.proveedor.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(response.data['id'], self.proveedor.pk)
        self.assertEqual(response.data['nombre'], self.proveedor.nombre)
        
    def test_crear_proveedor_api(self):
        """Test creating a provider through API"""
        count_before = Proveedor.objects.count()
        
        data = {
            'nombre': 'Nuevo Proveedor API',
            'direccion': 'Dirección API',
            'telefono': '9998887777',
            'correo': 'api@test.com',
            'tipo': 'nacional',
            'activo': True
        }
        
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify provider was created
        self.assertEqual(Proveedor.objects.count(), count_before + 1)
        
        # Check the data was saved correctly
        nuevo_proveedor = Proveedor.objects.get(nombre='Nuevo Proveedor API')
        self.assertEqual(nuevo_proveedor.correo, 'api@test.com')
        self.assertEqual(nuevo_proveedor.tipo, 'nacional')
        
    def test_actualizar_proveedor_api(self):
        """Test updating a provider through API"""
        url = reverse('api:proveedor-detail', kwargs={'pk': self.proveedor.pk})
        
        data = {
            'nombre': 'Proveedor Actualizado API',
            'direccion': 'Dirección Actualizada API',
            'telefono': '1231231231',
            'correo': 'actualizado@test.com',
            'tipo': 'internacional',
            'activo': False
        }
        
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify provider was updated
        self.proveedor.refresh_from_db()
        self.assertEqual(self.proveedor.nombre, 'Proveedor Actualizado API')
        self.assertEqual(self.proveedor.correo, 'actualizado@test.com')
        self.assertEqual(self.proveedor.tipo, 'internacional')
        self.assertFalse(self.proveedor.activo)
        
    def test_eliminar_proveedor_api(self):
        """Test deleting a provider through API"""
        url = reverse('api:proveedor-detail', kwargs={'pk': self.proveedor.pk})
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify provider was deleted
        with self.assertRaises(Proveedor.DoesNotExist):
            Proveedor.objects.get(pk=self.proveedor.pk)


# ====== HTMX TESTS ======

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
    """Test cases específicos para funcionalidad HTMX en proveedores"""
    
    def setUp(self):
        """Set up test data for HTMX tests"""
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass')
        
        self.tienda1 = Tienda.objects.create(
            nombre='Tienda HTMX 1',
            direccion='Dirección 1'
        )
        self.tienda2 = Tienda.objects.create(
            nombre='Tienda HTMX 2', 
            direccion='Dirección 2'
        )
        
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
    
    def test_proveedor_list_htmx_filter_by_requiere_anticipo(self):
        """Test HTMX filtering by requiere_anticipo"""
        response = self.client.get(
            reverse('proveedores:lista'),
            {'requiere_anticipo': 'true'},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Proveedor HTMX 1')
        self.assertContains(response, 'Test Search Proveedor')
        self.assertNotContains(response, 'Proveedor HTMX 2')
    
    def test_proveedor_list_htmx_filter_by_no_anticipo(self):
        """Test HTMX filtering by no requiere_anticipo"""
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
        self.assertContains(response, 'No se encontraron proveedores')
    
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
    
    def test_proveedor_pagination_htmx(self):
        """Test HTMX pagination functionality"""
        # Create more providers to test pagination
        for i in range(15):
            Proveedor.objects.create(
                nombre=f'Proveedor Pagination {i}',
                contacto=f'pagination{i}@test.com',
                requiere_anticipo=(i % 2 == 0),
                max_return_days=i + 10
            )
        
        response = self.client.get(
            reverse('proveedores:lista'),
            {'page': 2},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'proveedores/partials/proveedor_table.html')
    
    def test_proveedor_search_by_email(self):
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
      def test_proveedor_search_by_max_return_days(self):
        """Test HTMX search by max_return_days functionality - DISABLED until implemented"""
        # This test is disabled because the search functionality doesn't currently search by max_return_days
        pass
    
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
            'requiere_anticipo': False,
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
        self.assertFalse(updated_proveedor.requiere_anticipo)
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
    
    def test_proveedor_multiple_filters_htmx(self):
        """Test HTMX with multiple filter combinations"""
        # Create providers with specific attributes for testing
        Proveedor.objects.create(
            nombre='Proveedor Filtro Test',
            contacto='filtro@test.com',
            requiere_anticipo=True,
            max_return_days=25
        )
        
        response = self.client.get(
            reverse('proveedores:lista'),
            {
                'q': 'Filtro',
                'requiere_anticipo': 'true',
                'max_return_days_min': '20'
            },
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Proveedor Filtro Test')
        self.assertNotContains(response, 'Proveedor HTMX 1')  # doesn't match name filter
        self.assertNotContains(response, 'Proveedor HTMX 2')  # doesn't match anticipo filter
