#!/usr/bin/env python
"""
Test script to check devolution data in the database
"""
import os
import sys
import django

# Add the project directory to the path
sys.path.append('c:\\catalog_pos')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from devoluciones.models import Devolucion

def check_devolution_data():
    print("=== Checking Devolution Data ===")
    
    # Get devolution with ID 1
    try:
        devolucion = Devolucion.objects.get(pk=1)
        print(f"Devolution ID: {devolucion.id}")
        print(f"Cliente: {devolucion.cliente}")
        print(f"Producto: {devolucion.producto}")
        print(f"Detalle Pedido: {devolucion.detalle_pedido}")
        
        if devolucion.detalle_pedido:
            print(f"Pedido ID: {devolucion.detalle_pedido.pedido.id}")
            print(f"Pedido: {devolucion.detalle_pedido.pedido}")
        else:
            print("No detalle_pedido associated!")
            
    except Devolucion.DoesNotExist:
        print("Devolution with ID 1 does not exist!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_devolution_data()
