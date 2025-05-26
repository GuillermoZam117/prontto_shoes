from django.test import TestCase
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
