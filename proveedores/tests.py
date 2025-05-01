"""
Pruebas automáticas para el endpoint de proveedores:
- Creación de proveedor
- Listado de proveedores
- Filtrado por nombre
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Proveedor
from django.contrib.auth import get_user_model

class ProveedorAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.proveedor_data = {
            'nombre': 'Proveedor Test',
            'contacto': 'contacto@proveedor.com',
            'requiere_anticipo': False
        }

    def test_create_proveedor(self):
        url = reverse('proveedor-list')
        response = self.client.post(url, self.proveedor_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Proveedor.objects.count(), 1)
        self.assertEqual(Proveedor.objects.get().nombre, 'Proveedor Test')

    def test_list_proveedores(self):
        Proveedor.objects.create(**self.proveedor_data)
        url = reverse('proveedor-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_proveedor_by_nombre(self):
        Proveedor.objects.create(**self.proveedor_data)
        url = reverse('proveedor-list') + '?nombre=Proveedor Test'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nombre'], 'Proveedor Test')
