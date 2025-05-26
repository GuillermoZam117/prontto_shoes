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

print('=== CREANDO DATOS DE PRUEBA ===')

# Obtener cajas de hoy
cajas_hoy = Caja.objects.filter(fecha=date.today())
print(f'Cajas de hoy: {cajas_hoy.count()}')

# Actualizar movimiento existente para que tenga el formato correcto
movimiento_existente = MovimientoCaja.objects.first()
if movimiento_existente and movimiento_existente.tipo_movimiento == 'egreso':
    movimiento_existente.tipo_movimiento = 'EGRESO'
    movimiento_existente.save()
    print('Movimiento existente actualizado')

# Crear movimientos para cada caja de hoy
for caja in cajas_hoy:
    print(f'Procesando caja {caja.id} de {caja.tienda.nombre}')
    
    # Verificar si ya tiene movimientos
    movs_existentes = MovimientoCaja.objects.filter(caja=caja).count()
    print(f'  Movimientos existentes: {movs_existentes}')
    
    if movs_existentes < 3:  # Crear al menos 3 movimientos por caja
        # Crear ingresos
        MovimientoCaja.objects.create(
            caja=caja,
            tipo_movimiento='INGRESO',
            descripcion=f'Venta matutina - {caja.tienda.nombre}',
            monto=Decimal('250.00'),
            referencia=f'VENTA-{caja.id}-001'
        )
        
        MovimientoCaja.objects.create(
            caja=caja,
            tipo_movimiento='INGRESO',
            descripcion=f'Venta vespertina - {caja.tienda.nombre}',
            monto=Decimal('180.00'),
            referencia=f'VENTA-{caja.id}-002'
        )
        
        # Crear egreso
        MovimientoCaja.objects.create(
            caja=caja,
            tipo_movimiento='EGRESO',
            descripcion=f'Gastos operativos - {caja.tienda.nombre}',
            monto=Decimal('75.00'),
            referencia=f'GASTO-{caja.id}-001'
        )
        
        print(f'  Creados 3 movimientos para caja {caja.id}')
      # Actualizar totales de la caja
    from django.db import models
    ingresos = MovimientoCaja.objects.filter(caja=caja, tipo_movimiento='INGRESO').aggregate(
        total=models.Sum('monto')
    )['total'] or Decimal('0')
    
    egresos = MovimientoCaja.objects.filter(caja=caja, tipo_movimiento='EGRESO').aggregate(
        total=models.Sum('monto')
    )['total'] or Decimal('0')
    
    caja.ingresos = ingresos
    caja.egresos = egresos
    caja.saldo_final = caja.fondo_inicial + ingresos - egresos
    caja.save()
    
    print(f'  Caja actualizada: Ingresos=${ingresos}, Egresos=${egresos}, Saldo=${caja.saldo_final}')

print('\n=== VERIFICACIÓN FINAL ===')
total_movimientos = MovimientoCaja.objects.count()
movimientos_hoy = MovimientoCaja.objects.filter(fecha=date.today()).count()
print(f'Total movimientos: {total_movimientos}')
print(f'Movimientos de hoy: {movimientos_hoy}')

print('\n=== RESUMEN POR TIPO ===')
ingresos_hoy = MovimientoCaja.objects.filter(fecha=date.today(), tipo_movimiento='INGRESO').count()
egresos_hoy = MovimientoCaja.objects.filter(fecha=date.today(), tipo_movimiento='EGRESO').count()
print(f'Ingresos hoy: {ingresos_hoy}')
print(f'Egresos hoy: {egresos_hoy}')
