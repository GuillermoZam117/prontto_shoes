from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Cliente
from tiendas.models import Tienda
from django.contrib.auth import get_user_model

class ClienteAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.tienda = Tienda.objects.create(nombre='Tienda Test', direccion='Calle 1')
        self.cliente_data = {
            'nombre': 'Cliente Test',
            'contacto': 'contacto@test.com',
            'observaciones': 'Observaciones',
            'saldo_a_favor': 0,
            'tienda': self.tienda.id
        }

    def test_create_cliente(self):
        url = reverse('cliente-list')
        response = self.client.post(url, self.cliente_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Cliente.objects.count(), 1)
        self.assertEqual(Cliente.objects.get().nombre, 'Cliente Test')

    def test_list_clientes(self):
        Cliente.objects.create(**self.cliente_data)
        url = reverse('cliente-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_cliente_by_nombre(self):
        Cliente.objects.create(**self.cliente_data)
        url = reverse('cliente-list') + '?nombre=Cliente Test'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nombre'], 'Cliente Test')
