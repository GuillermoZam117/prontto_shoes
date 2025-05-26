from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
import json
import os
from decimal import Decimal

from productos.models import Producto, Catalogo
from productos.views import ProductoViewSet, CatalogoViewSet
from productos.serializers import ProductoSerializer, CatalogoSerializer
from tiendas.models import Tienda
from proveedores.models import Proveedor
from inventario.models import Inventario


class ProductoViewSetTestCase(APITestCase):
    """Test suite for ProductoViewSet"""
    
    def setUp(self):
        """Set up test data"""
        # Create user and authenticate
        self.user = get_user_model().objects.create_user(
            username='testuser', 
            password='testpass'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create related objects
        self.tienda = Tienda.objects.create(
            nombre='Tienda Test', 
            direccion='Calle 1'
        )
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Test'
        )
        self.catalogo = Catalogo.objects.create(
            nombre='Catálogo Test',
            temporada='2025',
            activo=True
        )
        self.catalogo_inactivo = Catalogo.objects.create(
            nombre='Catálogo Inactivo',
            temporada='2024',
            activo=False
        )
        
        # Create a product
        self.producto = Producto.objects.create(
            codigo='P001',
            marca='MarcaX',
            modelo='ModeloY',
            color='Rojo',
            talla='42',
            costo=Decimal('100.00'),
            precio=Decimal('150.00'),
            numero_pagina='10',
            temporada='Verano',
            oferta=False,
            admite_devolucion=True,
            proveedor=self.proveedor,
            tienda=self.tienda,
            catalogo=self.catalogo
        )
        
        # Create inventory for the product
        self.inventario = Inventario.objects.create(
            producto=self.producto,
            tienda=self.tienda,
            existencias=10,
            minimo=1,
            maximo=20
        )
        
        # Set up URLs
        self.list_url = reverse('producto-list')
        self.detail_url = reverse('producto-detail', kwargs={'pk': self.producto.pk})
        self.import_url = reverse('producto-import-excel')
        self.active_catalog_url = reverse('producto-active-catalog')

    def test_list_productos(self):
        """Test retrieving a list of products"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['codigo'], 'P001')

    def test_retrieve_producto(self):
        """Test retrieving a single product"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['codigo'], 'P001')
        self.assertEqual(response.data['marca'], 'MarcaX')

    def test_create_producto(self):
        """Test creating a new product"""
        new_product_data = {
            'codigo': 'P002',
            'marca': 'MarcaZ',
            'modelo': 'ModeloZ',
            'color': 'Azul',
            'talla': '38',
            'costo': '120.00',
            'precio': '180.00',
            'numero_pagina': '15',
            'temporada': 'Invierno',
            'oferta': True,
            'admite_devolucion': True,
            'proveedor': self.proveedor.id,
            'tienda': self.tienda.id,
            'catalogo': self.catalogo.id
        }
        
        response = self.client.post(self.list_url, new_product_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Producto.objects.count(), 2)
        
        # Verify the created product
        created_product = Producto.objects.get(codigo='P002')
        self.assertEqual(created_product.marca, 'MarcaZ')
        self.assertEqual(created_product.precio, Decimal('180.00'))

    def test_update_producto(self):
        """Test updating an existing product"""
        update_data = {
            'codigo': 'P001',
            'marca': 'MarcaActualizada',
            'modelo': 'ModeloY',
            'color': 'Rojo',
            'talla': '42',
            'costo': '100.00',
            'precio': '160.00',  # Updated price
            'numero_pagina': '10',
            'temporada': 'Verano',
            'oferta': True,  # Updated to True
            'admite_devolucion': True,
            'proveedor': self.proveedor.id,
            'tienda': self.tienda.id,
            'catalogo': self.catalogo.id
        }
        
        response = self.client.put(self.detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the updated product
        updated_product = Producto.objects.get(pk=self.producto.pk)
        self.assertEqual(updated_product.marca, 'MarcaActualizada')
        self.assertEqual(updated_product.precio, Decimal('160.00'))
        self.assertTrue(updated_product.oferta)

    def test_partial_update_producto(self):
        """Test partially updating a product"""
        patch_data = {
            'precio': '175.00',
            'oferta': True
        }
        
        response = self.client.patch(self.detail_url, patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the updated product
        updated_product = Producto.objects.get(pk=self.producto.pk)
        self.assertEqual(updated_product.precio, Decimal('175.00'))
        self.assertTrue(updated_product.oferta)
        # Other fields should remain unchanged
        self.assertEqual(updated_product.marca, 'MarcaX')

    def test_delete_producto(self):
        """Test deleting a product"""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Producto.objects.count(), 0)

    def test_filter_productos_by_marca(self):
        """Test filtering products by brand"""
        # Create another product with different brand
        Producto.objects.create(
            codigo='P003',
            marca='OtraMarca',
            modelo='ModeloA',
            color='Verde',
            talla='40',
            costo=Decimal('90.00'),
            precio=Decimal('140.00'),
            catalogo=self.catalogo,
            proveedor=self.proveedor,
            tienda=self.tienda
        )
        
        # Filter by the original brand
        url = f"{self.list_url}?marca=MarcaX"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['marca'], 'MarcaX')
        
        # Filter by the new brand
        url = f"{self.list_url}?marca=OtraMarca"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['marca'], 'OtraMarca')

    def test_search_productos(self):
        """Test searching products"""
        # Create products with searchable attributes
        Producto.objects.create(
            codigo='SEARCH001',
            marca='SearchMarca',
            modelo='SearchModelo',
            color='Negro',
            talla='41',
            costo=Decimal('95.00'),
            precio=Decimal('145.00'),
            catalogo=self.catalogo,
            proveedor=self.proveedor,
            tienda=self.tienda
        )
        
        # Search by code
        url = f"{self.list_url}?search=SEARCH001"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['codigo'], 'SEARCH001')
        
        # Search by brand
        url = f"{self.list_url}?search=SearchMarca"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['marca'], 'SearchMarca')
        
        # Search with no results
        url = f"{self.list_url}?search=NonExistent"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    @patch('pandas.read_excel')
    def test_import_excel_success(self, mock_read_excel):
        """Test successfully importing products from Excel"""
        # Mock pandas read_excel function
        mock_df = MagicMock()
        mock_read_excel.return_value = mock_df
        
        # Create a dummy Excel file
        excel_content = b'dummy excel content'
        excel_file = SimpleUploadedFile(
            name='test_products.xlsx',
            content=excel_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Make the request
        response = self.client.post(
            self.import_url,
            {'file': excel_file},
            format='multipart'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Importación exitosa')
        
        # Verify pandas was called with the uploaded file
        mock_read_excel.assert_called_once()

    def test_import_excel_no_file(self):
        """Test import Excel endpoint with no file"""
        response = self.client.post(self.import_url, {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'No se proporcionó ningún archivo')

    @patch('pandas.read_excel')
    def test_import_excel_exception(self, mock_read_excel):
        """Test handling exceptions during Excel import"""
        # Mock pandas to raise an exception
        mock_read_excel.side_effect = Exception('Test error')
        
        # Create a dummy Excel file
        excel_content = b'dummy excel content'
        excel_file = SimpleUploadedFile(
            name='test_products.xlsx',
            content=excel_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Make the request
        response = self.client.post(
            self.import_url,
            {'file': excel_file},
            format='multipart'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Test error')

    def test_active_catalog_products(self):
        """Test getting products from active catalog"""
        # Create another product in the active catalog
        producto2 = Producto.objects.create(
            codigo='P004',
            marca='MarcaActive',
            modelo='ModeloActive',
            color='Blanco',
            talla='39',
            costo=Decimal('110.00'),
            precio=Decimal('165.00'),
            catalogo=self.catalogo,  # Active catalog
            proveedor=self.proveedor,
            tienda=self.tienda
        )
        
        # Create product in inactive catalog
        producto3 = Producto.objects.create(
            codigo='P005',
            marca='MarcaInactive',
            modelo='ModeloInactive',
            color='Azul',
            talla='43',
            costo=Decimal('120.00'),
            precio=Decimal('180.00'),
            catalogo=self.catalogo_inactivo,  # Inactive catalog
            proveedor=self.proveedor,
            tienda=self.tienda
        )
        
        # Create inventory for these products
        Inventario.objects.create(
            producto=producto2,
            tienda=self.tienda,
            existencias=5,
            minimo=1,
            maximo=10
        )
        
        Inventario.objects.create(
            producto=producto3,
            tienda=self.tienda,
            existencias=8,
            minimo=1,
            maximo=15
        )
        
        # Get products from active catalog
        response = self.client.get(self.active_catalog_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return only products from active catalog
        product_codes = [item['codigo'] for item in response.data]
        self.assertIn('P001', product_codes)
        self.assertIn('P004', product_codes)
        self.assertNotIn('P005', product_codes)
        
        # Check if inventory data is included
        for item in response.data:
            if 'cantidad_disponible' in item:
                if item['codigo'] == 'P001':
                    self.assertEqual(item['cantidad_disponible'], 10)
                elif item['codigo'] == 'P004':
                    self.assertEqual(item['cantidad_disponible'], 5)

    def test_active_catalog_no_active_catalogs(self):
        """Test getting products when no catalogs are active"""
        # Deactivate all catalogs
        Catalogo.objects.all().update(activo=False)
        
        response = self.client.get(self.active_catalog_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], 'No hay catálogos activos en este momento.')


class CatalogoViewSetTestCase(APITestCase):
    """Test suite for CatalogoViewSet"""
    
    def setUp(self):
        """Set up test data"""
        # Create user and authenticate
        self.user = get_user_model().objects.create_user(
            username='testuser', 
            password='testpass'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create catalogs
        self.catalogo1 = Catalogo.objects.create(
            nombre='Catálogo Primavera',
            temporada='Primavera 2025',
            es_oferta=False,
            activo=True,
            fecha_inicio_vigencia=timezone.now().date(),
            fecha_fin_vigencia=timezone.now().date() + timezone.timedelta(days=90)
        )
        
        self.catalogo2 = Catalogo.objects.create(
            nombre='Catálogo Verano',
            temporada='Verano 2025',
            es_oferta=False,
            activo=False,
            fecha_inicio_vigencia=timezone.now().date() + timezone.timedelta(days=91),
            fecha_fin_vigencia=timezone.now().date() + timezone.timedelta(days=180)
        )
        
        self.catalogo_oferta = Catalogo.objects.create(
            nombre='Catálogo Ofertas',
            temporada='Ofertas 2025',
            es_oferta=True,
            activo=True,
            fecha_inicio_vigencia=timezone.now().date(),
            fecha_fin_vigencia=timezone.now().date() + timezone.timedelta(days=30)
        )
        
        # Set up URLs
        self.list_url = reverse('catalogo-list')
        self.detail_url = reverse('catalogo-detail', kwargs={'pk': self.catalogo1.pk})
        self.activar_url = reverse('catalogo-activar-catalogo')

    def test_list_catalogos(self):
        """Test retrieving a list of catalogs"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_retrieve_catalogo(self):
        """Test retrieving a single catalog"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nombre'], 'Catálogo Primavera')
        self.assertEqual(response.data['temporada'], 'Primavera 2025')

    def test_create_catalogo(self):
        """Test creating a new catalog"""
        new_catalog_data = {
            'nombre': 'Catálogo Otoño',
            'temporada': 'Otoño 2025',
            'es_oferta': False,
            'activo': False,
            'fecha_inicio_vigencia': (timezone.now().date() + timezone.timedelta(days=181)).isoformat(),
            'fecha_fin_vigencia': (timezone.now().date() + timezone.timedelta(days=270)).isoformat()
        }
        
        response = self.client.post(self.list_url, new_catalog_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Catalogo.objects.count(), 4)
        
        # Verify the created catalog
        created_catalog = Catalogo.objects.get(nombre='Catálogo Otoño')
        self.assertEqual(created_catalog.temporada, 'Otoño 2025')
        self.assertFalse(created_catalog.activo)

    def test_update_catalogo(self):
        """Test updating an existing catalog"""
        update_data = {
            'nombre': 'Catálogo Primavera Actualizado',
            'temporada': 'Primavera 2025',
            'es_oferta': False,
            'activo': True,
            'fecha_inicio_vigencia': self.catalogo1.fecha_inicio_vigencia.isoformat(),
            'fecha_fin_vigencia': self.catalogo1.fecha_fin_vigencia.isoformat()
        }
        
        response = self.client.put(self.detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the updated catalog
        updated_catalog = Catalogo.objects.get(pk=self.catalogo1.pk)
        self.assertEqual(updated_catalog.nombre, 'Catálogo Primavera Actualizado')

    def test_activar_catalogo_basic(self):
        """Test activating a catalog without deactivating others"""
        # Deactivate catalogo1 first
        self.catalogo1.activo = False
        self.catalogo1.save()
        
        data = {
            'catalogo_id': self.catalogo1.id
        }
        
        response = self.client.post(self.activar_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify catalogo1 is now active
        self.catalogo1.refresh_from_db()
        self.assertTrue(self.catalogo1.activo)
        
        # Verify catalogo_oferta is still active
        self.catalogo_oferta.refresh_from_db()
        self.assertTrue(self.catalogo_oferta.activo)

    def test_activar_catalogo_deactivate_others_temporada(self):
        """Test activating a catalog and deactivating others of same season"""
        # Create another catalog of the same season
        catalogo_same_season = Catalogo.objects.create(
            nombre='Catálogo Primavera 2',
            temporada='Primavera 2025',  # Same as catalogo1
            es_oferta=False,
            activo=True
        )
        
        data = {
            'catalogo_id': self.catalogo1.id,
            'desactivar_otros_temporada': True
        }
        
        response = self.client.post(self.activar_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify catalogo1 is active
        self.catalogo1.refresh_from_db()
        self.assertTrue(self.catalogo1.activo)
        
        # Verify catalogo_same_season is now inactive
        catalogo_same_season.refresh_from_db()
        self.assertFalse(catalogo_same_season.activo)
        
        # Verify catalogo_oferta is still active (different season)
        self.catalogo_oferta.refresh_from_db()
        self.assertTrue(self.catalogo_oferta.activo)

    def test_activar_catalogo_deactivate_others_oferta(self):
        """Test activating a catalog and deactivating other offer catalogs"""
        # Create another offer catalog
        catalogo_oferta2 = Catalogo.objects.create(
            nombre='Catálogo Ofertas 2',
            temporada='Ofertas 2 2025',
            es_oferta=True,
            activo=True
        )
        
        data = {
            'catalogo_id': self.catalogo_oferta.id,
            'desactivar_otros_oferta': True
        }
        
        response = self.client.post(self.activar_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify catalogo_oferta is active
        self.catalogo_oferta.refresh_from_db()
        self.assertTrue(self.catalogo_oferta.activo)
        
        # Verify catalogo_oferta2 is now inactive
        catalogo_oferta2.refresh_from_db()
        self.assertFalse(catalogo_oferta2.activo)
        
        # Verify catalogo1 is still active (not an offer)
        self.catalogo1.refresh_from_db()
        self.assertTrue(self.catalogo1.activo)

    def test_activar_catalogo_deactivate_all(self):
        """Test activating a catalog and deactivating all others"""
        data = {
            'catalogo_id': self.catalogo2.id,
            'desactivar_todos_anteriores': True
        }
        
        response = self.client.post(self.activar_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify catalogo2 is now active
        self.catalogo2.refresh_from_db()
        self.assertTrue(self.catalogo2.activo)
        
        # Verify all other catalogs are inactive
        self.catalogo1.refresh_from_db()
        self.catalogo_oferta.refresh_from_db()
        self.assertFalse(self.catalogo1.activo)
        self.assertFalse(self.catalogo_oferta.activo)

    def test_activar_catalogo_invalid_id(self):
        """Test activating a catalog with invalid ID"""
        data = {
            'catalogo_id': 999  # Non-existent ID
        }
        
        response = self.client.post(self.activar_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Catálogo no encontrado.')

    def test_activar_catalogo_missing_id(self):
        """Test activating a catalog without providing an ID"""
        data = {}
        
        response = self.client.post(self.activar_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Debe proporcionar el ID del catálogo a activar.')

    def test_filter_catalogos_by_temporada(self):
        """Test filtering catalogs by season"""
        url = f"{self.list_url}?temporada=Primavera 2025"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nombre'], 'Catálogo Primavera')
          def test_filter_catalogos_by_activo(self):
        """Test filtering catalogs by active status"""
        url = f"{self.list_url}?activo=true"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # catalogo1 and catalogo_oferta
        
        url = f"{self.list_url}?activo=false"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # catalogo2
        
    def test_producto_filtro_marca(self):
        """Test filtering products by brand"""
        # Create another product with different brand
        Producto.objects.create(
            codigo='TEST123',
            nombre='Producto Test Marca',
            descripcion='Test',
            precio_compra=Decimal('50.00'),
            precio_venta=Decimal('100.00'),
            marca='OTRA_MARCA',
            catalogo=self.catalogo1,
            activo=True
        )
        
        url = f"{self.producto_list_url}?marca=MARCA_TEST"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        for producto in response.data:
            self.assertEqual(producto['marca'], 'MARCA_TEST')
            
        url = f"{self.producto_list_url}?marca=OTRA_MARCA"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        for producto in response.data:
            self.assertEqual(producto['marca'], 'OTRA_MARCA')
    
    def test_producto_busqueda_codigo(self):
        """Test searching products by code"""
        url = f"{self.producto_list_url}?search=PROD001"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        for producto in response.data:
            self.assertTrue('PROD001' in producto['codigo'])
    
    def test_producto_ordenamiento(self):
        """Test ordering products"""
        # Create products with different prices
        Producto.objects.create(
            codigo='BARATO001',
            nombre='Producto Barato',
            descripcion='Test',
            precio_compra=Decimal('10.00'),
            precio_venta=Decimal('20.00'),
            marca='MARCA_TEST',
            catalogo=self.catalogo1,
            activo=True
        )
        
        Producto.objects.create(
            codigo='CARO001',
            nombre='Producto Caro',
            descripcion='Test',
            precio_compra=Decimal('100.00'),
            precio_venta=Decimal('200.00'),
            marca='MARCA_TEST',
            catalogo=self.catalogo1,
            activo=True
        )
        
        # Order by precio_venta ascending
        url = f"{self.producto_list_url}?ordering=precio_venta"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 3)
        
        precios = [Decimal(producto['precio_venta']) for producto in response.data]
        self.assertEqual(precios, sorted(precios))
        
        # Order by precio_venta descending
        url = f"{self.producto_list_url}?ordering=-precio_venta"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        precios = [Decimal(producto['precio_venta']) for producto in response.data]
        self.assertEqual(precios, sorted(precios, reverse=True))
    
    def test_producto_inventario(self):
        """Test inventory endpoint for products"""
        # Ensure inventory exists
        inventario, created = Inventario.objects.get_or_create(
            producto=self.producto,
            tienda=self.tienda,
            defaults={'cantidad': 10}
        )
        if not created:
            inventario.cantidad = 10
            inventario.save()
            
        url = reverse('api:producto-inventory', kwargs={'pk': self.producto.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        
        # Check inventory data
        found = False
        for item in response.data:
            if item['tienda']['id'] == self.tienda.id:
                self.assertEqual(item['cantidad'], 10)
                found = True
                break
        
        self.assertTrue(found, "Inventory for test store not found")
    
    def test_producto_disponibilidad(self):
        """Test checking product availability"""
        # Ensure inventory exists
        inventario, created = Inventario.objects.get_or_create(
            producto=self.producto,
            tienda=self.tienda,
            defaults={'cantidad': 5}
        )
        if not created:
            inventario.cantidad = 5
            inventario.save()
            
        url = f"{self.producto_list_url}?disponible=true"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should include our test product with inventory
        producto_ids = [p['id'] for p in response.data]
        self.assertIn(self.producto.id, producto_ids)
        
        # Create product with no inventory
        producto_sin_stock = Producto.objects.create(
            codigo='NOSTOCK001',
            nombre='Producto Sin Stock',
            descripcion='Test',
            precio_compra=Decimal('50.00'),
            precio_venta=Decimal('100.00'),
            marca='MARCA_TEST',
            catalogo=self.catalogo1,
            activo=True
        )
        
        # Filter for products with no inventory
        url = f"{self.producto_list_url}?disponible=false"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should include our product with no inventory
        producto_ids = [p['id'] for p in response.data]
        self.assertIn(producto_sin_stock.id, producto_ids)
        
    def test_catalogo_productos_endpoint(self):
        """Test getting products for a specific catalog"""
        url = reverse('api:catalogo-productos', kwargs={'pk': self.catalogo1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # All products should belong to this catalog
        for producto in response.data:
            self.assertEqual(producto['catalogo'], self.catalogo1.id)
