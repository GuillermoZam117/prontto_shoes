"""
Pruebas automáticas para el endpoint de tiendas:
- Creación de tienda
- Listado de tiendas
- Filtrado por nombre
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Tienda
from django.contrib.auth import get_user_model

class TiendaAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.tienda_data = {
            'nombre': 'Tienda Test',
            'direccion': 'Calle 1',
            'contacto': 'contacto@tienda.com',
            'activa': True
        }

    def test_create_tienda(self):
        url = reverse('tienda-list')
        response = self.client.post(url, self.tienda_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tienda.objects.count(), 1)
        self.assertEqual(Tienda.objects.get().nombre, 'Tienda Test')

    def test_list_tiendas(self):
        Tienda.objects.create(**self.tienda_data)
        url = reverse('tienda-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_tienda_by_nombre(self):
        Tienda.objects.create(**self.tienda_data)
        url = reverse('tienda-list') + '?nombre=Tienda Test'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nombre'], 'Tienda Test')
