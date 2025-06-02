#!/usr/bin/env python
"""
Script para verificar que los modelos de pedidos avanzados se crearon correctamente
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from pedidos_avanzados.models import (
    OrdenCliente, EstadoProductoSeguimiento, EntregaParcial, 
    NotaCredito, PortalClientePolitica, ProductoCompartir
)

def verificar_modelos():
    """Verificar que todos los modelos se pueden importar y usar"""
    
    print("🔍 Verificando modelos de Pedidos Avanzados...")
    print("=" * 60)
    
    # Verificar cada modelo
    modelos = [
        ("OrdenCliente", OrdenCliente),
        ("EstadoProductoSeguimiento", EstadoProductoSeguimiento),
        ("EntregaParcial", EntregaParcial),
        ("NotaCredito", NotaCredito),
        ("PortalClientePolitica", PortalClientePolitica),
        ("ProductoCompartir", ProductoCompartir),
    ]
    
    for nombre, modelo in modelos:
        try:
            # Verificar que podemos hacer query al modelo
            count = modelo.objects.count()
            print(f"✅ {nombre}: OK (Registros: {count})")
        except Exception as e:
            print(f"❌ {nombre}: ERROR - {e}")
    
    print("\n📊 Verificando estructura de OrdenCliente...")
    # Verificar campos específicos de OrdenCliente
    try:
        fields = [f.name for f in OrdenCliente._meta.fields]
        print(f"   Campos: {', '.join(fields)}")
    except Exception as e:
        print(f"   Error al obtener campos: {e}")
    
    print("\n📊 Verificando estructura de EstadoProductoSeguimiento...")
    # Verificar opciones de estado
    try:
        estados = EstadoProductoSeguimiento.ESTADO_CHOICES
        print(f"   Estados disponibles: {len(estados)} opciones")
        for codigo, nombre in estados:
            print(f"   - {codigo}: {nombre}")
    except Exception as e:
        print(f"   Error al obtener estados: {e}")
    
    print("\n🎯 Verificación completada!")

if __name__ == "__main__":
    verificar_modelos()
