from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Producto
from tiendas.models import Tienda
from proveedores.models import Proveedor
from django.contrib.auth import get_user_model

class ProductoAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.tienda = Tienda.objects.create(nombre='Tienda Test', direccion='Calle 1')
        self.proveedor = Proveedor.objects.create(nombre='Proveedor Test')
        self.producto_data = {
            'codigo': 'P001',
            'marca': 'MarcaX',
            'modelo': 'ModeloY',
            'color': 'Rojo',
            'propiedad': 'Talla 26',
            'costo': 100.0,
            'precio': 150.0,
            'numero_pagina': '10',
            'temporada': 'Verano',
            'oferta': False,
            'admite_devolucion': True,
            'proveedor': self.proveedor.id,
            'tienda': self.tienda.id
        }

    def test_create_producto(self):
        url = reverse('producto-list')
        response = self.client.post(url, self.producto_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Producto.objects.count(), 1)
        self.assertEqual(Producto.objects.get().codigo, 'P001')

    def test_list_productos(self):
        Producto.objects.create(**self.producto_data)
        url = reverse('producto-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_producto_by_codigo(self):
        Producto.objects.create(**self.producto_data)
        url = reverse('producto-list') + '?codigo=P001'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['codigo'], 'P001')
