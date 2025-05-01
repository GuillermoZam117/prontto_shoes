"""
Pruebas automáticas para el endpoint de anticipos:
- Creación de anticipo
- Listado de anticipos
- Filtrado por cliente
"""
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from clientes.models import Anticipo, Cliente
from tiendas.models import Tienda
from django.contrib.auth import get_user_model

class AnticipoAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.tienda = Tienda.objects.create(nombre='Tienda Test', direccion='Calle 1')
        self.cliente = Cliente.objects.create(nombre='Cliente Test', tienda=self.tienda)
        self.anticipo_data = {
            'cliente': self.cliente.id,
            'monto': 100.0,
            'fecha': '2025-05-01'
        }

    def test_create_anticipo(self):
        url = reverse('anticipo-list')
        response = self.client.post(url, self.anticipo_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Anticipo.objects.count(), 1)
        self.assertEqual(Anticipo.objects.get().cliente, self.cliente)

    def test_list_anticipos(self):
        Anticipo.objects.create(**self.anticipo_data)
        url = reverse('anticipo-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_anticipo_by_cliente(self):
        Anticipo.objects.create(**self.anticipo_data)
        url = reverse('anticipo-list') + f'?cliente={self.cliente.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['cliente'], self.cliente.id)
