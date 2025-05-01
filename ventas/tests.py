from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Pedido
from clientes.models import Cliente
from tiendas.models import Tienda
from django.contrib.auth import get_user_model

class PedidoAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.tienda = Tienda.objects.create(nombre='Tienda Test', direccion='Calle 1')
        self.cliente = Cliente.objects.create(nombre='Cliente Test', tienda=self.tienda)
        self.pedido_data = {
            'cliente': self.cliente.id,
            'fecha': '2025-05-01T10:00:00Z',
            'estado': 'pendiente',
            'total': 100.0,
            'tienda': self.tienda.id,
            'tipo': 'venta',
            'descuento_aplicado': 0
        }

    def test_create_pedido(self):
        url = reverse('pedido-list')
        response = self.client.post(url, self.pedido_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Pedido.objects.count(), 1)
        self.assertEqual(Pedido.objects.get().cliente, self.cliente)

    def test_list_pedidos(self):
        Pedido.objects.create(**self.pedido_data)
        url = reverse('pedido-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_pedido_by_estado(self):
        Pedido.objects.create(**self.pedido_data)
        url = reverse('pedido-list') + '?estado=pendiente'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['estado'], 'pendiente')

"""
Pruebas automáticas para el endpoint de detalles de pedido:
- Creación de detalle de pedido
- Listado de detalles de pedido
- Filtrado por pedido
"""
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import DetallePedido, Pedido
from productos.models import Producto
from clientes.models import Cliente
from tiendas.models import Tienda
from proveedores.models import Proveedor
from django.contrib.auth import get_user_model

class DetallePedidoAPITestCase(APITestCase):
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
        self.cliente = Cliente.objects.create(nombre='Cliente Test', tienda=self.tienda)
        self.pedido = Pedido.objects.create(
            cliente=self.cliente, fecha='2025-05-01T10:00:00Z', estado='pendiente', total=100.0,
            tienda=self.tienda, tipo='venta', descuento_aplicado=0
        )
        self.detalle_data = {
            'pedido': self.pedido.id,
            'producto': self.producto.id,
            'cantidad': 2,
            'precio_unitario': 150.0,
            'subtotal': 300.0
        }

    def test_create_detalle_pedido(self):
        url = reverse('detallepedido-list')
        response = self.client.post(url, self.detalle_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DetallePedido.objects.count(), 1)
        self.assertEqual(DetallePedido.objects.get().pedido, self.pedido)

    def test_list_detalles_pedido(self):
        DetallePedido.objects.create(**self.detalle_data)
        url = reverse('detallepedido-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_detalle_by_pedido(self):
        DetallePedido.objects.create(**self.detalle_data)
        url = reverse('detallepedido-list') + f'?pedido={self.pedido.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['pedido'], self.pedido.id)
