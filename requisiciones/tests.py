"""
Pruebas automáticas para el endpoint de requisiciones:
- Creación de requisición
- Listado de requisiciones
- Filtrado por estado
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Requisicion
from clientes.models import Cliente
from tiendas.models import Tienda
from django.contrib.auth import get_user_model

class RequisicionAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.tienda = Tienda.objects.create(nombre='Tienda Test', direccion='Calle 1')
        self.cliente = Cliente.objects.create(nombre='Cliente Test', tienda=self.tienda)
        self.requisicion_data = {
            'cliente': self.cliente.id,
            'estado': 'pendiente'
        }

    def test_create_requisicion(self):
        url = reverse('requisicion-list')
        response = self.client.post(url, self.requisicion_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Requisicion.objects.count(), 1)
        self.assertEqual(Requisicion.objects.get().estado, 'pendiente')

    def test_list_requisiciones(self):
        Requisicion.objects.create(**self.requisicion_data)
        url = reverse('requisicion-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_requisicion_by_estado(self):
        Requisicion.objects.create(**self.requisicion_data)
        url = reverse('requisicion-list') + '?estado=pendiente'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['estado'], 'pendiente')

"""
Pruebas automáticas para el endpoint de detalles de requisición:
- Creación de detalle de requisición
- Listado de detalles de requisición
- Filtrado por requisición
"""
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import DetalleRequisicion, Requisicion
from productos.models import Producto
from clientes.models import Cliente
from tiendas.models import Tienda
from proveedores.models import Proveedor
from django.contrib.auth import get_user_model

class DetalleRequisicionAPITestCase(APITestCase):
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
        self.requisicion = Requisicion.objects.create(cliente=self.cliente, estado='pendiente')
        self.detalle_data = {
            'requisicion': self.requisicion.id,
            'producto': self.producto.id,
            'cantidad': 2
        }

    def test_create_detalle_requisicion(self):
        url = reverse('detallerequisicion-list')
        response = self.client.post(url, self.detalle_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DetalleRequisicion.objects.count(), 1)
        self.assertEqual(DetalleRequisicion.objects.get().requisicion, self.requisicion)

    def test_list_detalles_requisicion(self):
        DetalleRequisicion.objects.create(**self.detalle_data)
        url = reverse('detallerequisicion-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_detalle_by_requisicion(self):
        DetalleRequisicion.objects.create(**self.detalle_data)
        url = reverse('detallerequisicion-list') + f'?requisicion={self.requisicion.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['requisicion'], self.requisicion.id)
