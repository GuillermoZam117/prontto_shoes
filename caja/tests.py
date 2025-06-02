"""
Tests completos para la aplicación de caja
Sistema POS Pronto Shoes
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import datetime, date, timedelta

from .models import Caja, NotaCargo, Factura, TransaccionCaja, MovimientoCaja
from tiendas.models import Tienda
from ventas.models import Pedido
from clientes.models import Cliente

User = get_user_model()


class CajaModelTestCase(TestCase):
    """Tests para el modelo Caja"""
    
    def setUp(self):
        self.tienda = Tienda.objects.create(
            nombre='Tienda Test',
            direccion='Calle 1',
            activa=True
        )
    
    def test_crear_caja(self):
        """Test crear caja"""
        caja = Caja.objects.create(
            tienda=self.tienda,
            fecha=date.today(),
            ingresos=Decimal('1000.00'),
            egresos=Decimal('500.00'),
            saldo_final=Decimal('500.00')
        )
        
        self.assertEqual(caja.tienda, self.tienda)
        self.assertEqual(caja.fecha, date.today())
        self.assertEqual(caja.ingresos, Decimal('1000.00'))
        self.assertEqual(caja.egresos, Decimal('500.00'))
        self.assertEqual(caja.saldo_final, Decimal('500.00'))
    
    def test_str_representation(self):
        """Test representación string de caja"""
        caja = Caja.objects.create(
            tienda=self.tienda,
            fecha=date.today(),
            ingresos=Decimal('1000.00'),
            egresos=Decimal('500.00'),
            saldo_final=Decimal('500.00')
        )
        
        expected = f"Caja {self.tienda.nombre} - {date.today()}"
        self.assertEqual(str(caja), expected)

class CajaAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.tienda = Tienda.objects.create(nombre='Tienda Test', direccion='Calle 1')
        self.caja_data = {
            'tienda': self.tienda.id,
            'fecha': '2025-05-01',
            'ingresos': 1000.0,
            'egresos': 500.0,
            'saldo_final': 500.0
        }

    def test_create_caja(self):
        url = reverse('caja-list')
        response = self.client.post(url, self.caja_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Caja.objects.count(), 1)
        self.assertEqual(Caja.objects.get().tienda, self.tienda)

    def test_list_cajas(self):
        Caja.objects.create(tienda=self.tienda, fecha='2025-05-01', ingresos=1000.0, egresos=500.0, saldo_final=500.0)
        url = reverse('caja-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_caja_by_tienda(self):
        Caja.objects.create(tienda=self.tienda, fecha='2025-05-01', ingresos=1000.0, egresos=500.0, saldo_final=500.0)
        url = reverse('caja-list') + f'?tienda={self.tienda.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['tienda'], self.tienda.id)

class NotaCargoAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.tienda = Tienda.objects.create(nombre='Tienda Test', direccion='Calle 1')
        self.caja = Caja.objects.create(tienda=self.tienda, fecha='2025-05-01', ingresos=1000, egresos=500, saldo_final=500)
        self.nota_data = {
            'caja': self.caja.id,
            'monto': 100.0,
            'motivo': 'Ajuste',
            'fecha': '2025-05-01'
        }

    def test_create_nota_cargo(self):
        url = reverse('notacargo-list')
        response = self.client.post(url, self.nota_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(NotaCargo.objects.count(), 1)
        self.assertEqual(NotaCargo.objects.get().caja, self.caja)

    def test_list_notas_cargo(self):
        NotaCargo.objects.create(caja=self.caja, monto=100.0, motivo='Ajuste', fecha='2025-05-01')
        url = reverse('notacargo-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_nota_cargo_by_caja(self):
        NotaCargo.objects.create(caja=self.caja, monto=100.0, motivo='Ajuste', fecha='2025-05-01')
        url = reverse('notacargo-list') + f'?caja={self.caja.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['caja'], self.caja.id)

class FacturaAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.tienda = Tienda.objects.create(nombre='Tienda Test', direccion='Calle 1')
        self.cliente = Cliente.objects.create(nombre='Cliente Test', tienda=self.tienda)
        self.pedido = Pedido.objects.create(cliente=self.cliente, fecha='2025-05-01T10:00:00Z', estado='pendiente', total=100.0, tienda=self.tienda, tipo='venta', descuento_aplicado=0)
        self.factura_data = {
            'pedido': self.pedido.id,
            'folio': 'F001',
            'fecha': '2025-05-01',
            'total': 100.0
        }

    def test_create_factura(self):
        url = reverse('factura-list')
        response = self.client.post(url, self.factura_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Factura.objects.count(), 1)
        self.assertEqual(Factura.objects.get().pedido, self.pedido)

    def test_list_facturas(self):
        Factura.objects.create(pedido=self.pedido, folio='F001', fecha='2025-05-01', total=100.0)
        url = reverse('factura-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_factura_by_pedido(self):
        Factura.objects.create(pedido=self.pedido, folio='F001', fecha='2025-05-01', total=100.0)
        url = reverse('factura-list') + f'?pedido={self.pedido.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['pedido'], self.pedido.id)

"""
Pruebas automáticas para el endpoint de facturas:
- Creación de factura
- Listado de facturas
- Filtrado por pedido
"""
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Factura, Caja
from ventas.models import Pedido
from tiendas.models import Tienda
from clientes.models import Cliente
from django.contrib.auth import get_user_model

class FacturaAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.tienda = Tienda.objects.create(nombre='Tienda Test', direccion='Calle 1')
        self.cliente = Cliente.objects.create(nombre='Cliente Test', tienda=self.tienda)
        self.pedido = Pedido.objects.create(cliente=self.cliente, fecha='2025-05-01T10:00:00Z', estado='pendiente', total=100.0, tienda=self.tienda, tipo='venta', descuento_aplicado=0)
        self.factura_data = {
            'pedido': self.pedido.id,
            'folio': 'F001',
            'fecha': '2025-05-01',
            'total': 100.0
        }

    def test_create_factura(self):
        url = reverse('factura-list')
        response = self.client.post(url, self.factura_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Factura.objects.count(), 1)
        self.assertEqual(Factura.objects.get().pedido, self.pedido)

    def test_list_facturas(self):
        Factura.objects.create(pedido=self.pedido, folio='F001', fecha='2025-05-01', total=100.0)
        url = reverse('factura-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_factura_by_pedido(self):
        Factura.objects.create(pedido=self.pedido, folio='F001', fecha='2025-05-01', total=100.0)
        url = reverse('factura-list') + f'?pedido={self.pedido.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['pedido'], self.pedido.id)
