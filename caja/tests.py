"""
Pruebas automáticas para el endpoint de caja:
- Creación de caja
- Listado de cajas
- Filtrado por tienda
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Caja
from tiendas.models import Tienda
from django.contrib.auth import get_user_model

class CajaAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.tienda = Tienda.objects.create(nombre='Tienda Test', direccion='Calle 1')
        self.caja_data = {
            'tienda': self.tienda.id,
            'fecha': '2025-05-01',
            'ingresos': 1000.0,
            'egresos': 500.0,
            'saldo_final': 500.0
        }

    def test_create_caja(self):
        url = reverse('caja-list')
        response = self.client.post(url, self.caja_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Caja.objects.count(), 1)
        self.assertEqual(Caja.objects.get().tienda, self.tienda)

    def test_list_cajas(self):
        Caja.objects.create(**self.caja_data)
        url = reverse('caja-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_caja_by_tienda(self):
        Caja.objects.create(**self.caja_data)
        url = reverse('caja-list') + f'?tienda={self.tienda.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['tienda'], self.tienda.id)
