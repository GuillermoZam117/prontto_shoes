from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Inventario
from tiendas.models import Tienda
from productos.models import Producto
from proveedores.models import Proveedor
from django.contrib.auth import get_user_model

class InventarioAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.tienda = Tienda.objects.create(nombre='Tienda Test', direccion='Calle 1')
        self.proveedor = Proveedor.objects.create(nombre='Proveedor Test')
        self.producto = Producto.objects.create(
            codigo='P001', marca='MarcaX', modelo='ModeloY', color='Rojo', propiedad='Talla 26',
            costo=100.0, precio=150.0, numero_pagina='10', temporada='Verano', oferta=False,
            admite_devolucion=True, proveedor=self.proveedor, tienda=self.tienda
        )
        self.inventario_data = {
            'tienda': self.tienda.id,
            'producto': self.producto.id,
            'cantidad_actual': 10,
            'fecha_registro': '2025-05-01'
        }

    def test_create_inventario(self):
        url = reverse('inventario-list')
        response = self.client.post(url, self.inventario_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Inventario.objects.count(), 1)
        self.assertEqual(Inventario.objects.get().producto, self.producto)

    def test_list_inventario(self):
        Inventario.objects.create(tienda=self.tienda, producto=self.producto, cantidad_actual=10, fecha_registro='2025-05-01')
        url = reverse('inventario-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_inventario_by_producto(self):
        Inventario.objects.create(tienda=self.tienda, producto=self.producto, cantidad_actual=10, fecha_registro='2025-05-01')
        url = reverse('inventario-list') + f'?producto={self.producto.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['producto'], self.producto.id)

"""
Pruebas automáticas para el endpoint de traspasos:
- Creación de traspaso
- Listado de traspasos
- Filtrado por producto
"""
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Traspaso
from tiendas.models import Tienda
from productos.models import Producto
from proveedores.models import Proveedor
from django.contrib.auth import get_user_model

class TraspasoAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.tienda_origen = Tienda.objects.create(nombre='Tienda Origen', direccion='Calle 1')
        self.tienda_destino = Tienda.objects.create(nombre='Tienda Destino', direccion='Calle 2')
        self.proveedor = Proveedor.objects.create(nombre='Proveedor Test')
        self.producto = Producto.objects.create(
            codigo='P001', marca='MarcaX', modelo='ModeloY', color='Rojo', propiedad='Talla 26',
            costo=100.0, precio=150.0, numero_pagina='10', temporada='Verano', oferta=False,
            admite_devolucion=True, proveedor=self.proveedor, tienda=self.tienda_origen
        )
        self.traspaso_data = {
            'producto': self.producto.id,
            'tienda_origen': self.tienda_origen.id,
            'tienda_destino': self.tienda_destino.id,
            'cantidad': 5,
            'fecha': '2025-05-01',
            'estado': 'pendiente'
        }

    def test_create_traspaso(self):
        url = reverse('traspaso-list')
        response = self.client.post(url, self.traspaso_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Traspaso.objects.count(), 1)
        self.assertEqual(Traspaso.objects.get().producto, self.producto)

    def test_list_traspasos(self):
        Traspaso.objects.create(producto=self.producto, tienda_origen=self.tienda_origen, tienda_destino=self.tienda_destino, cantidad=5, fecha='2025-05-01', estado='pendiente')
        url = reverse('traspaso-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_traspaso_by_producto(self):
        Traspaso.objects.create(producto=self.producto, tienda_origen=self.tienda_origen, tienda_destino=self.tienda_destino, cantidad=5, fecha='2025-05-01', estado='pendiente')
        url = reverse('traspaso-list') + f'?producto={self.producto.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['producto'], self.producto.id)
