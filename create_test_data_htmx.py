#!/usr/bin/env python
"""
Script para generar datos de prueba para validar funcionalidad HTMX
Sistema POS Pronto Shoes - Testing Implementation
"""

import os
import sys
import django
from decimal import Decimal
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from django.contrib.auth.models import User
from tiendas.models import Tienda
from clientes.models import Cliente, Anticipo
from proveedores.models import Proveedor
from productos.models import Producto, Catalogo
from ventas.models import Pedido

def create_test_data():
    """Crear datos de prueba para testing HTMX"""
    
    print("🏗️  Creando datos de prueba para Sistema POS...")
    
    # Crear usuarios de prueba si no existen
    user, created = User.objects.get_or_create(
        username='admin02',
        defaults={
            'email': 'admin@prontoshoes.com',
            'first_name': 'Admin',
            'last_name': 'ProntoShoes',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        user.set_password('admin123')
        user.save()
        print("✅ Usuario admin02 creado")
    
    # Crear tiendas
    tiendas_data = [
        {'nombre': 'Pronto Shoes Centro', 'direccion': 'Av. Central 123'},
        {'nombre': 'Pronto Shoes Plaza Norte', 'direccion': 'Plaza Norte Local 45'},
        {'nombre': 'Pronto Shoes Mall Sur', 'direccion': 'Mall Sur Piso 2'}
    ]
    
    tiendas = []
    for data in tiendas_data:
        tienda, created = Tienda.objects.get_or_create(
            nombre=data['nombre'],
            defaults=data
        )
        tiendas.append(tienda)
        if created:
            print(f"✅ Tienda creada: {tienda.nombre}")
    
    # Crear clientes de prueba
    clientes_data = [
        {
            'nombre': 'María García López',
            'contacto': '555-1234',
            'saldo_a_favor': Decimal('150.00'),
            'monto_acumulado': Decimal('2500.00')
        },
        {
            'nombre': 'Juan Carlos Méndez',
            'contacto': '555-5678',
            'saldo_a_favor': Decimal('0.00'),
            'monto_acumulado': Decimal('1800.00')
        },
        {
            'nombre': 'Ana Patricia Rivera',
            'contacto': '555-9876',
            'saldo_a_favor': Decimal('75.00'),
            'monto_acumulado': Decimal('950.00')
        },
        {
            'nombre': 'Roberto Silva Castro',
            'contacto': '555-4321',
            'saldo_a_favor': Decimal('200.00'),
            'monto_acumulado': Decimal('3200.00')
        },
        {
            'nombre': 'Carmen Flores Vega',
            'contacto': '555-8765',
            'saldo_a_favor': Decimal('0.00'),
            'monto_acumulado': Decimal('750.00')
        },
        {
            'nombre': 'Cliente Para Eliminar',
            'contacto': '555-0000',
            'saldo_a_favor': Decimal('0.00'),
            'monto_acumulado': Decimal('0.00')
        }
    ]
    
    clientes = []
    for i, data in enumerate(clientes_data):
        data['tienda'] = tiendas[i % len(tiendas)]
        cliente, created = Cliente.objects.get_or_create(
            nombre=data['nombre'],
            defaults=data
        )
        clientes.append(cliente)
        if created:
            print(f"✅ Cliente creado: {cliente.nombre}")
    
    # Crear anticipos para algunos clientes
    anticipos_data = [
        {'cliente': clientes[0], 'monto': Decimal('100.00'), 'utilizado': False},
        {'cliente': clientes[0], 'monto': Decimal('50.00'), 'utilizado': True},
        {'cliente': clientes[3], 'monto': Decimal('200.00'), 'utilizado': False},
    ]
    
    for data in anticipos_data:
        anticipo, created = Anticipo.objects.get_or_create(
            cliente=data['cliente'],
            monto=data['monto'],
            defaults=data
        )
        if created:
            print(f"✅ Anticipo creado: ${anticipo.monto} para {anticipo.cliente.nombre}")
    
    # Crear proveedores de prueba
    proveedores_data = [
        {
            'nombre': 'Calzado Comfort SA',
            'contacto': 'ventas@comfort.com',
            'telefono': '555-1111'
        },
        {
            'nombre': 'Distribuidora Fashion',
            'contacto': 'pedidos@fashion.com', 
            'telefono': '555-2222'
        },
        {
            'nombre': 'Zapatos Premium LTDA',
            'contacto': 'info@premium.com',
            'telefono': '555-3333'
        },
        {
            'nombre': 'Proveedor Para Eliminar',
            'contacto': 'test@eliminar.com',
            'telefono': '555-0000'
        }
    ]
    
    proveedores = []
    for data in proveedores_data:
        proveedor, created = Proveedor.objects.get_or_create(
            nombre=data['nombre'],
            defaults=data
        )
        proveedores.append(proveedor)
        if created:
            print(f"✅ Proveedor creado: {proveedor.nombre}")
    
    # Crear algunos productos básicos
    if not Producto.objects.exists():
        productos_data = [
            {
                'nombre': 'Zapato Casual Negro',
                'codigo': 'ZCN001',
                'precio': Decimal('299.99')
            },
            {
                'nombre': 'Tenis Deportivos',
                'codigo': 'TD002', 
                'precio': Decimal('450.00')
            },
            {
                'nombre': 'Sandalia Verano',
                'codigo': 'SV003',
                'precio': Decimal('199.99')
            }
        ]
        
        for data in productos_data:
            producto, created = Producto.objects.get_or_create(
                codigo=data['codigo'],
                defaults=data
            )
            if created:
                print(f"✅ Producto creado: {producto.nombre}")
    
    print(f"\n🎯 DATOS DE PRUEBA CREADOS:")
    print(f"   👥 Clientes: {Cliente.objects.count()}")
    print(f"   🏢 Proveedores: {Proveedor.objects.count()}")
    print(f"   🏪 Tiendas: {Tienda.objects.count()}")
    print(f"   👟 Productos: {Producto.objects.count()}")
    print(f"   💰 Anticipos: {Anticipo.objects.count()}")
    
    print(f"\n✅ TESTING PREPARADO:")
    print(f"   🔍 Buscar: 'María', 'Juan', 'Cliente Para'")
    print(f"   🗑️  Eliminar: 'Cliente Para Eliminar' (sin restricciones)")
    print(f"   🗑️  Eliminar: 'María García' (con saldo - debe fallar)")
    print(f"   🗑️  Eliminar: 'Roberto Silva' (con anticipo - debe fallar)")
    
    return {
        'users': User.objects.count(),
        'tiendas': Tienda.objects.count(),
        'clientes': Cliente.objects.count(),
        'proveedores': Proveedor.objects.count(),
        'productos': Producto.objects.count(),
        'anticipos': Anticipo.objects.count()
    }

if __name__ == '__main__':
    try:
        stats = create_test_data()
        print(f"\n🚀 DATOS DE PRUEBA LISTOS PARA HTMX TESTING!")
        print(f"📊 Total registros creados: {sum(stats.values())}")
        
    except Exception as e:
        print(f"❌ Error creando datos de prueba: {e}")
        sys.exit(1)
