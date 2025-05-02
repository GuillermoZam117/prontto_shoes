"""
Pruebas automáticas para el endpoint de devoluciones:
- Creación de devolución
- Listado de devoluciones
- Filtrado por tipo
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Devolucion
from clientes.models import Cliente
from productos.models import Producto
from tiendas.models import Tienda
from proveedores.models import Proveedor
from django.contrib.auth import get_user_model

class DevolucionAPITestCase(APITestCase):
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
        self.devolucion_data = {
            'cliente': self.cliente.id,
            'producto': self.producto.id,
            'tipo': 'defecto',
            'motivo': 'Defecto de fábrica',
            'estado': 'pendiente',
            'confirmacion_proveedor': False,
            'afecta_inventario': True,
            'saldo_a_favor_generado': 0
        }

    def test_create_devolucion(self):
        url = reverse('devolucion-list')
        response = self.client.post(url, self.devolucion_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Devolucion.objects.count(), 1)
        self.assertEqual(Devolucion.objects.get().tipo, 'defecto')

    def test_list_devoluciones(self):
        Devolucion.objects.create(cliente=self.cliente, producto=self.producto, tipo='defecto', motivo='Defecto de fábrica', estado='pendiente', confirmacion_proveedor=False, afecta_inventario=True, saldo_a_favor_generado=0)
        url = reverse('devolucion-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_devolucion_by_tipo(self):
        Devolucion.objects.create(cliente=self.cliente, producto=self.producto, tipo='defecto', motivo='Defecto de fábrica', estado='pendiente', confirmacion_proveedor=False, afecta_inventario=True, saldo_a_favor_generado=0)
        url = reverse('devolucion-list') + '?tipo=defecto'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['tipo'], 'defecto')
