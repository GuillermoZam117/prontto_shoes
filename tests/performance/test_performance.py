"""
Performance tests for the Django POS system
"""
import pytest
import time
from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.db import connection
from django.test.utils import override_settings
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

from tests.factories import (
    UserFactory, TiendaFactory, ClienteFactory, ProductoFactory,
    ProveedorFactory, PedidoFactory, DetallePedidoFactory,
    InventarioFactory, CajaFactory, TransaccionCajaFactory
)
from ventas.models import Pedido, DetallePedido
from inventario.models import Inventario
from productos.models import Producto
from clientes.models import Cliente


class PerformanceTestCase(TransactionTestCase):
    """Base class for performance tests"""
    
    def setUp(self):
        self.start_time = time.time()
        self.query_count_start = len(connection.queries)
        
    def tearDown(self):
        end_time = time.time()
        execution_time = end_time - self.start_time
        query_count = len(connection.queries) - self.query_count_start
        
        print(f"\nTest execution time: {execution_time:.4f}s")
        print(f"Database queries: {query_count}")
        
        # Performance thresholds
        if execution_time > 5.0:  # 5 seconds
            self.fail(f"Test took too long: {execution_time:.4f}s")
        if query_count > 100:  # 100 queries
            self.fail(f"Too many database queries: {query_count}")


class BulkDataPerformanceTest(PerformanceTestCase):
    """Tests for bulk data operations performance"""
    
    def test_bulk_product_creation_performance(self):
        """Test creating many products quickly"""
        proveedor = ProveedorFactory()
        tienda = TiendaFactory()
        
        start_time = time.time()
        
        # Create 100 products
        productos = []
        for i in range(100):
            productos.append(ProductoFactory.build(
                codigo=f"PERF{i:05d}",
                proveedor=proveedor,
                tienda=tienda
            ))
        
        # Bulk create
        Producto.objects.bulk_create(productos)
        
        creation_time = time.time() - start_time
        self.assertLess(creation_time, 2.0, "Bulk product creation should be fast")
        
        # Verify all were created
        self.assertEqual(Producto.objects.filter(codigo__startswith='PERF').count(), 100)
    
    def test_bulk_order_processing_performance(self):
        """Test processing multiple orders efficiently"""
        cliente = ClienteFactory()
        productos = ProductoFactory.create_batch(10)
        
        start_time = time.time()
        
        # Create 50 orders with multiple items each
        for i in range(50):
            pedido = PedidoFactory(cliente=cliente)
            
            # Add 3-5 products to each order
            for j in range(3):
                DetallePedidoFactory(
                    pedido=pedido,
                    producto=productos[j],
                    cantidad=1,
                    precio_unitario=productos[j].precio
                )
        
        processing_time = time.time() - start_time
        self.assertLess(processing_time, 3.0, "Bulk order processing should be efficient")
        
        # Verify orders were created
        self.assertEqual(Pedido.objects.filter(cliente=cliente).count(), 50)
    
    def test_inventory_bulk_updates_performance(self):
        """Test bulk inventory updates"""
        tienda = TiendaFactory()
        productos = ProductoFactory.create_batch(50, tienda=tienda)
        
        # Create initial inventory
        inventarios = []
        for producto in productos:
            inventarios.append(InventarioFactory.build(
                producto=producto,
                tienda=tienda,
                cantidad_actual=100
            ))
        
        Inventario.objects.bulk_create(inventarios)
        
        start_time = time.time()
        
        # Bulk update inventory
        inventario_updates = []
        for inventario in Inventario.objects.filter(tienda=tienda):
            inventario.cantidad_actual = 150
            inventario_updates.append(inventario)
        
        Inventario.objects.bulk_update(inventario_updates, ['cantidad_actual'])
        
        update_time = time.time() - start_time
        self.assertLess(update_time, 1.0, "Bulk inventory updates should be fast")


class QueryOptimizationTest(PerformanceTestCase):
    """Tests for query optimization"""
    
    def test_pedido_with_detalles_query_optimization(self):
        """Test optimized queries for order with details"""
        cliente = ClienteFactory()
        pedido = PedidoFactory(cliente=cliente)
        DetallePedidoFactory.create_batch(5, pedido=pedido)
        
        # Test unoptimized query
        start_queries = len(connection.queries)
        pedidos_unoptimized = list(Pedido.objects.all())
        for pedido in pedidos_unoptimized:
            list(pedido.detalles.all())  # This creates N+1 queries
        unoptimized_queries = len(connection.queries) - start_queries
        
        # Reset query log
        connection.queries_log.clear()
        
        # Test optimized query with prefetch_related
        start_queries = len(connection.queries)
        pedidos_optimized = list(Pedido.objects.prefetch_related('detalles').all())
        for pedido in pedidos_optimized:
            list(pedido.detalles.all())  # This should not create additional queries
        optimized_queries = len(connection.queries) - start_queries
        
        self.assertLess(optimized_queries, unoptimized_queries, 
                       "Optimized query should use fewer database calls")
    
    def test_cliente_pedidos_query_optimization(self):
        """Test optimized queries for client orders"""
        cliente = ClienteFactory()
        PedidoFactory.create_batch(3, cliente=cliente)
        
        # Test with select_related optimization
        start_time = time.time()
        pedidos = list(Pedido.objects.select_related('cliente', 'tienda').all())
        query_time = time.time() - start_time
        
        self.assertLess(query_time, 0.5, "Optimized client-order query should be fast")
        
        # Verify no additional queries when accessing related fields
        start_queries = len(connection.queries)
        for pedido in pedidos:
            _ = pedido.cliente.nombre
            _ = pedido.tienda.nombre
        additional_queries = len(connection.queries) - start_queries
        
        self.assertEqual(additional_queries, 0, 
                        "No additional queries should be made with select_related")


class ConcurrencyTest(TransactionTestCase):
    """Tests for concurrent operations"""
    
    def test_concurrent_inventory_updates(self):
        """Test handling concurrent inventory updates"""
        from django.db import transaction
        from threading import Thread
        import threading
        
        producto = ProductoFactory()
        tienda = TiendaFactory()
        inventario = InventarioFactory(
            producto=producto,
            tienda=tienda,
            cantidad_actual=100
        )
        
        results = []
        errors = []
        
        def update_inventory(amount):
            try:
                with transaction.atomic():
                    inv = Inventario.objects.select_for_update().get(id=inventario.id)
                    new_amount = inv.cantidad_actual - amount
                    inv.cantidad_actual = new_amount
                    inv.save()
                    results.append(new_amount)
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads that try to update inventory simultaneously
        threads = []
        for i in range(5):
            thread = Thread(target=update_inventory, args=(10,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that updates were handled correctly
        self.assertEqual(len(errors), 0, f"No errors should occur: {errors}")
        
        # Refresh from database
        inventario.refresh_from_db()
        self.assertEqual(inventario.cantidad_actual, 50, 
                        "Inventory should be correctly updated after concurrent operations")


class LoadTestCase(PerformanceTestCase):
    """Load testing scenarios"""
    
    def test_high_volume_order_creation(self):
        """Test system performance under high order volume"""
        clientes = ClienteFactory.create_batch(10)
        productos = ProductoFactory.create_batch(20)
        
        start_time = time.time()
        
        # Simulate high volume of orders
        for i in range(100):
            cliente = clientes[i % 10]
            pedido = PedidoFactory(cliente=cliente)
            
            # Add 2-3 products per order
            for j in range(2):
                producto = productos[(i + j) % 20]
                DetallePedidoFactory(
                    pedido=pedido,
                    producto=producto,
                    cantidad=1,
                    precio_unitario=producto.precio
                )
        
        total_time = time.time() - start_time
        self.assertLess(total_time, 10.0, "High volume order creation should complete in reasonable time")
        
        # Verify all orders were created
        self.assertEqual(Pedido.objects.count(), 100)
        self.assertEqual(DetallePedido.objects.count(), 200)
    
    def test_reporting_query_performance(self):
        """Test performance of reporting queries"""
        # Create test data
        clientes = ClienteFactory.create_batch(5)
        productos = ProductoFactory.create_batch(10)
        
        # Create orders over time period
        for i in range(50):
            fecha = timezone.now() - timedelta(days=i)
            cliente = clientes[i % 5]
            pedido = PedidoFactory(cliente=cliente, fecha=fecha)
            
            for j in range(2):
                producto = productos[j % 10]
                DetallePedidoFactory(
                    pedido=pedido,
                    producto=producto,
                    cantidad=1,
                    precio_unitario=producto.precio
                )
        
        # Test reporting query performance
        start_time = time.time()
        
        # Complex reporting query
        from django.db.models import Sum, Count, Avg
        report_data = (
            Pedido.objects
            .select_related('cliente', 'tienda')
            .prefetch_related('detalles__producto')
            .aggregate(
                total_orders=Count('id'),
                total_revenue=Sum('total'),
                average_order_value=Avg('total')
            )
        )
        
        query_time = time.time() - start_time
        self.assertLess(query_time, 2.0, "Reporting queries should be fast")
        
        # Verify report data
        self.assertEqual(report_data['total_orders'], 50)
        self.assertIsNotNone(report_data['total_revenue'])


@pytest.mark.performance
class MemoryUsageTest(TestCase):
    """Tests for memory usage optimization"""
    
    def test_memory_efficient_bulk_operations(self):
        """Test memory usage during bulk operations"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large dataset
        tienda = TiendaFactory()
        proveedor = ProveedorFactory()
        
        # Use iterator to avoid loading all objects into memory
        productos = (
            ProductoFactory.build(
                codigo=f"MEM{i:06d}",
                tienda=tienda,
                proveedor=proveedor
            )
            for i in range(1000)
        )
        
        # Bulk create in batches
        batch_size = 100
        batch = []
        for producto in productos:
            batch.append(producto)
            if len(batch) >= batch_size:
                Producto.objects.bulk_create(batch)
                batch = []
        
        if batch:
            Producto.objects.bulk_create(batch)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        self.assertLess(memory_increase, 50, 
                       f"Memory usage should be reasonable: {memory_increase:.2f}MB")
        
        # Verify all products were created
        self.assertEqual(Producto.objects.filter(codigo__startswith='MEM').count(), 1000)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
