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
        Pedido.objects.create(cliente=self.cliente, fecha='2025-05-01T10:00:00Z', estado='pendiente', total=100.0, tienda=self.tienda, tipo='venta', descuento_aplicado=0)
        url = reverse('pedido-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_pedido_by_estado(self):
        Pedido.objects.create(cliente=self.cliente, fecha='2025-05-01T10:00:00Z', estado='pendiente', total=100.0, tienda=self.tienda, tipo='venta', descuento_aplicado=0)
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
        DetallePedido.objects.create(pedido=self.pedido, producto=self.producto, cantidad=2, precio_unitario=150.0, subtotal=300.0)
        url = reverse('detallepedido-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_detalle_by_pedido(self):
        DetallePedido.objects.create(pedido=self.pedido, producto=self.producto, cantidad=2, precio_unitario=150.0, subtotal=300.0)
        url = reverse('detallepedido-list') + f'?pedido={self.pedido.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['pedido'], self.pedido.id)

class ApartadosPorClienteReporteAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser2', password='testpass2')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.tienda = Tienda.objects.create(nombre='Tienda Test', direccion='Calle 1')
        self.cliente1 = Cliente.objects.create(nombre='Cliente Uno', tienda=self.tienda)
        self.cliente2 = Cliente.objects.create(nombre='Cliente Dos', tienda=self.tienda)
        self.pedido1 = Pedido.objects.create(cliente=self.cliente1, fecha='2025-05-01', estado='pendiente', total=100.0, tienda=self.tienda, tipo='venta', descuento_aplicado=0)
        self.pedido2 = Pedido.objects.create(cliente=self.cliente2, fecha='2025-05-02', estado='pendiente', total=200.0, tienda=self.tienda, tipo='venta', descuento_aplicado=0)
        self.pedido3 = Pedido.objects.create(cliente=self.cliente1, fecha='2025-05-03', estado='completado', total=150.0, tienda=self.tienda, tipo='venta', descuento_aplicado=0)
        self.proveedor = Proveedor.objects.create(nombre='Proveedor Test')
        self.producto = Producto.objects.create(
            codigo='P002', marca='MarcaY', modelo='ModeloZ', color='Azul', propiedad='Talla 27',
            costo=120.0, precio=180.0, numero_pagina='11', temporada='Invierno', oferta=False,
            admite_devolucion=True, proveedor=self.proveedor, tienda=self.tienda
        )
        DetallePedido.objects.create(pedido=self.pedido1, producto=self.producto, cantidad=1, precio_unitario=180.0, subtotal=180.0)
        DetallePedido.objects.create(pedido=self.pedido2, producto=self.producto, cantidad=2, precio_unitario=180.0, subtotal=360.0)

    def test_apartados_por_cliente_reporte_basic(self):
        url = '/api/reportes/apartados_por_cliente/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)

    def test_apartados_por_cliente_reporte_filter_cliente(self):
        url = f'/api/reportes/apartados_por_cliente/?cliente_id={self.cliente1.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['cliente_id'], self.cliente1.id)

    def test_apartados_por_cliente_reporte_filter_fecha(self):
        url = '/api/reportes/apartados_por_cliente/?fecha_desde=2025-05-02&fecha_hasta=2025-05-02'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['cliente_id'], self.cliente2.id)

    def test_apartados_por_cliente_reporte_pagination(self):
        url = '/api/reportes/apartados_por_cliente/?limit=1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIn('count', response.data)

class PedidosPorSurtirReporteAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Crear tiendas
        self.tienda1 = Tienda.objects.create(nombre='Tienda Uno', direccion='Calle 1')
        self.tienda2 = Tienda.objects.create(nombre='Tienda Dos', direccion='Calle 2')
        
        # Crear clientes
        self.cliente1 = Cliente.objects.create(nombre='Cliente Uno', tienda=self.tienda1)
        self.cliente2 = Cliente.objects.create(nombre='Cliente Dos', tienda=self.tienda2)
        
        # Crear proveedor y productos
        self.proveedor = Proveedor.objects.create(nombre='Proveedor Test')
        self.producto1 = Producto.objects.create(
            codigo='P001', marca='MarcaX', modelo='ModeloY', color='Rojo',
            propiedad='Talla 26', costo=100.0, precio=150.0,
            numero_pagina='10', temporada='Verano', oferta=False,
            admite_devolucion=True, proveedor=self.proveedor, tienda=self.tienda1
        )
        self.producto2 = Producto.objects.create(
            codigo='P002', marca='MarcaY', modelo='ModeloZ', color='Azul',
            propiedad='Talla 27', costo=120.0, precio=180.0,
            numero_pagina='11', temporada='Verano', oferta=False,
            admite_devolucion=True, proveedor=self.proveedor, tienda=self.tienda2
        )
        
        # Crear pedidos de prueba
        self.pedido1 = Pedido.objects.create(
            cliente=self.cliente1,
            fecha='2025-05-01T10:00:00Z',
            estado='pendiente',
            total=300.0,
            tienda=self.tienda1,
            tipo='venta',
            descuento_aplicado=0
        )
        self.pedido2 = Pedido.objects.create(
            cliente=self.cliente2,
            fecha='2025-05-02T10:00:00Z',
            estado='completado',
            total=360.0,
            tienda=self.tienda2,
            tipo='venta',
            descuento_aplicado=0
        )
        
        # Crear detalles de pedido
        DetallePedido.objects.create(
            pedido=self.pedido1,
            producto=self.producto1,
            cantidad=2,
            precio_unitario=150.0,
            subtotal=300.0
        )
        DetallePedido.objects.create(
            pedido=self.pedido2,
            producto=self.producto2,
            cantidad=2,
            precio_unitario=180.0,
            subtotal=360.0
        )

    def test_pedidos_reporte_basic(self):
        url = '/api/reportes/pedidos_por_surtir/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data['results'][0]
        self.assertIn('totales', data)
        self.assertIn('pendientes', data)
        self.assertIn('completados', data)
        self.assertEqual(data['totales']['total_pedidos'], 2)

    def test_pedidos_reporte_filter_cliente(self):
        url = f'/api/reportes/pedidos_por_surtir/?cliente_id={self.cliente1.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data['results'][0]
        self.assertEqual(len(data['pendientes']['pedidos']), 1)
        self.assertEqual(data['pendientes']['pedidos'][0]['cliente']['id'], self.cliente1.id)

    def test_pedidos_reporte_filter_tienda(self):
        url = f'/api/reportes/pedidos_por_surtir/?tienda_id={self.tienda1.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data['results'][0]
        pedidos_tienda = data['pendientes']['pedidos'] + data['completados']['pedidos']
        self.assertTrue(all(p['tienda']['id'] == self.tienda1.id for p in pedidos_tienda))

    def test_pedidos_reporte_filter_estado(self):
        url = '/api/reportes/pedidos_por_surtir/?estado=completado'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data['results'][0]
        self.assertEqual(data['completados']['total_pedidos'], 1)
        self.assertEqual(len(data['pendientes']['pedidos']), 0)

    def test_pedidos_reporte_filter_fecha(self):
        url = '/api/reportes/pedidos_por_surtir/?fecha_desde=2025-05-02'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data['results'][0]
        todos_pedidos = data['pendientes']['pedidos'] + data['completados']['pedidos']
        self.assertTrue(all(p['fecha'][:10] >= '2025-05-02' for p in todos_pedidos))

    def test_pedidos_reporte_detalles_productos(self):
        url = f'/api/reportes/pedidos_por_surtir/?cliente_id={self.cliente1.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data['results'][0]
        productos = data['pendientes']['pedidos'][0]['productos']
        self.assertEqual(len(productos), 1)
        self.assertIn('codigo', productos[0])
        self.assertIn('marca', productos[0])
        self.assertIn('modelo', productos[0])
        self.assertIn('proveedor', productos[0])
        self.assertEqual(float(productos[0]['subtotal']), 300.0)

    def test_pedidos_reporte_totales(self):
        url = '/api/reportes/pedidos_por_surtir/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data['results'][0]
        self.assertEqual(float(data['totales']['monto_total']), 660.0)
        self.assertEqual(data['pendientes']['total_pedidos'] + data['completados']['total_pedidos'], 2)