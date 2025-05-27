#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from caja.models import Caja
from tiendas.models import Tienda
from datetime import date

today = date.today()
print('=== DIAGNÓSTICO CAJA ===')
print(f'Fecha actual: {today}')
print()

print('Tiendas:')
tiendas = Tienda.objects.all()
for tienda in tiendas:
    print(f'  {tienda.id}: {tienda.nombre}')
print()

print('Cajas abiertas hoy:')
cajas_hoy = Caja.objects.filter(fecha=today, cerrada=False)
for caja in cajas_hoy:
    print(f'  Caja {caja.id}: Tienda {caja.tienda.id} ({caja.tienda.nombre}) - Fondo: ${caja.fondo_inicial}')

if not cajas_hoy.exists():
    print('  ¡No hay cajas abiertas hoy!')
    print()
    print('Todas las cajas (últimas 5):')
    for caja in Caja.objects.all().order_by('-fecha')[:5]:
        print(f'  Caja {caja.id}: Tienda {caja.tienda.id} ({caja.tienda.nombre}) - Fecha: {caja.fecha} - Cerrada: {caja.cerrada}')

print()
print('=== SOLUCIÓN ===')
if not cajas_hoy.exists() and tiendas.exists():
    primera_tienda = tiendas.first()
    print(f'Vamos a abrir una caja para la tienda: {primera_tienda.nombre}')
    
    nueva_caja = Caja.objects.create(
        tienda=primera_tienda,
        fecha=today,
        fondo_inicial=1000.00,
        saldo_final=1000.00,
        cerrada=False
    )
    print(f'¡Caja creada! ID: {nueva_caja.id} para tienda {primera_tienda.nombre}')
else:
    print('Ya hay cajas abiertas o no hay tiendas disponibles.')
