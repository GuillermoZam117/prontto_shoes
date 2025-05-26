#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from caja.models import Caja, MovimientoCaja
from tiendas.models import Tienda
from datetime import date
from decimal import Decimal

print('=== DIAGNÓSTICO DE PROBLEMAS ===')

# 1. Verificar cajas existentes
cajas = Caja.objects.all()
print(f'Cajas totales: {cajas.count()}')

# 2. Verificar movimientos de caja
movimientos = MovimientoCaja.objects.all()
print(f'Movimientos totales: {movimientos.count()}')

# 3. Verificar cajas de hoy
cajas_hoy = Caja.objects.filter(fecha=date.today())
print(f'Cajas de hoy: {cajas_hoy.count()}')

# 4. Verificar movimientos de hoy
movimientos_hoy = MovimientoCaja.objects.filter(fecha=date.today())
print(f'Movimientos de hoy: {movimientos_hoy.count()}')

# 5. Mostrar algunas cajas para debug
print('\n=== CAJAS EXISTENTES ===')
for caja in cajas[:5]:
    print(f'Caja {caja.id}: {caja.tienda.nombre} - {caja.fecha} - Cerrada: {caja.cerrada}')

# 6. Mostrar algunos movimientos
print('\n=== MOVIMIENTOS EXISTENTES ===')
for mov in movimientos[:5]:
    print(f'Mov {mov.id}: {mov.caja.tienda.nombre} - {mov.fecha} - {mov.tipo} - Monto: {mov.monto}')

# 7. Verificar tiendas
tiendas = Tienda.objects.all()
print(f'\n=== TIENDAS ===')
for tienda in tiendas:
    print(f'Tienda {tienda.id}: {tienda.nombre}')

# 8. Crear movimientos de prueba para hoy si no existen
if movimientos_hoy.count() == 0:
    print('\n=== CREANDO DATOS DE PRUEBA PARA HOY ===')
    
    # Crear caja para hoy si no existe
    tienda = tiendas.first()
    if tienda:
        caja_hoy, created = Caja.objects.get_or_create(
            tienda=tienda,
            fecha=date.today(),
            defaults={
                'fondo_inicial': Decimal('1000.00'),
                'cerrada': False
            }
        )
        print(f'Caja creada/encontrada: {caja_hoy.id}')
        
        # Crear algunos movimientos
        MovimientoCaja.objects.create(
            caja=caja_hoy,
            tipo_movimiento='INGRESO',
            descripcion='Venta de prueba',
            monto=Decimal('150.00'),
            referencia='VENTA-001'
        )
        
        MovimientoCaja.objects.create(
            caja=caja_hoy,
            tipo_movimiento='EGRESO',
            descripcion='Compra de insumos',
            monto=Decimal('50.00'),
            referencia='COMPRA-001'
        )
        
        print('Movimientos de prueba creados')

print('\n=== VERIFICACIÓN FINAL ===')
print(f'Movimientos de hoy después: {MovimientoCaja.objects.filter(fecha=date.today()).count()}')
