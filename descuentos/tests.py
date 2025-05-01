"""
Pruebas automáticas para el endpoint de tabulador de descuentos:
- Creación de tabulador
- Listado de tabuladores
- Filtrado por porcentaje
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import TabuladorDescuento
from django.contrib.auth import get_user_model

class TabuladorDescuentoAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.tabulador_data = {
            'rango_min': 0,
            'rango_max': 1000,
            'porcentaje': 10
        }

    def test_create_tabulador(self):
        url = reverse('tabuladordescuento-list')
        response = self.client.post(url, self.tabulador_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TabuladorDescuento.objects.count(), 1)
        self.assertEqual(TabuladorDescuento.objects.get().porcentaje, 10)

    def test_list_tabuladores(self):
        TabuladorDescuento.objects.create(**self.tabulador_data)
        url = reverse('tabuladordescuento-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_tabulador_by_porcentaje(self):
        TabuladorDescuento.objects.create(**self.tabulador_data)
        url = reverse('tabuladordescuento-list') + '?porcentaje=10'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['porcentaje'], 10)
