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
from decimal import Decimal

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

class DevolucionesReporteAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.tienda = Tienda.objects.create(nombre='Tienda Test', direccion='Calle 1')
        
        # Crear clientes de prueba
        self.cliente1 = Cliente.objects.create(nombre='Cliente Uno', tienda=self.tienda)
        self.cliente2 = Cliente.objects.create(nombre='Cliente Dos', tienda=self.tienda)
        
        # Crear proveedor y productos
        self.proveedor = Proveedor.objects.create(nombre='Proveedor Test')
        self.producto1 = Producto.objects.create(
            codigo='P001', marca='MarcaX', modelo='ModeloY', color='Rojo',
            propiedad='Talla 26', costo=100.0, precio=150.0,
            numero_pagina='10', temporada='Verano', oferta=False,
            admite_devolucion=True, proveedor=self.proveedor, tienda=self.tienda
        )
        self.producto2 = Producto.objects.create(
            codigo='P002', marca='MarcaY', modelo='ModeloZ', color='Azul',
            propiedad='Talla 27', costo=120.0, precio=180.0,
            numero_pagina='11', temporada='Verano', oferta=False,
            admite_devolucion=True, proveedor=self.proveedor, tienda=self.tienda
        )
        
        # Crear devoluciones de prueba
        self.devolucion1 = Devolucion.objects.create(
            cliente=self.cliente1, producto=self.producto1,
            tipo='defecto', motivo='Defecto de fábrica',
            estado='pendiente', confirmacion_proveedor=False,
            afecta_inventario=True, saldo_a_favor_generado=Decimal('150.00')
        )
        self.devolucion2 = Devolucion.objects.create(
            cliente=self.cliente2, producto=self.producto2,
            tipo='cambio', motivo='Talla incorrecta',
            estado='validada', confirmacion_proveedor=True,
            afecta_inventario=True, saldo_a_favor_generado=Decimal('180.00')
        )

    def test_devoluciones_reporte_basic(self):
        url = '/api/reportes/devoluciones/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # 2 clientes con devoluciones

    def test_devoluciones_reporte_filter_cliente(self):
        url = f'/api/reportes/devoluciones/?cliente_id={self.cliente1.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['cliente_id'], self.cliente1.id)
        self.assertEqual(response.data['results'][0]['total_devoluciones'], 1)

    def test_devoluciones_reporte_filter_tipo(self):
        url = '/api/reportes/devoluciones/?tipo=defecto'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['results']
        self.assertTrue(any(dev['tipo'] == 'defecto' 
                          for cliente in data 
                          for dev in cliente['devoluciones']))

    def test_devoluciones_reporte_filter_estado(self):
        url = '/api/reportes/devoluciones/?estado=validada'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['results']
        self.assertTrue(any(dev['estado'] == 'validada' 
                          for cliente in data 
                          for dev in cliente['devoluciones']))

    def test_devoluciones_reporte_pagination(self):
        url = '/api/reportes/devoluciones/?limit=1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIn('count', response.data)
        self.assertTrue(response.data['count'] >= 2)  # Al menos 2 clientes en total

    def test_devoluciones_reporte_totals(self):
        url = f'/api/reportes/devoluciones/?cliente_id={self.cliente1.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cliente_data = response.data['results'][0]
        self.assertEqual(cliente_data['total_devoluciones'], 1)
        self.assertEqual(float(cliente_data['saldo_a_favor_total']), 150.00)
