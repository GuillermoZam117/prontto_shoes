from django.db import models
from proveedores.models import Proveedor
from tiendas.models import Tienda
from django.contrib.auth import get_user_model

class Catalogo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    temporada = models.CharField(max_length=50, blank=True, null=True)
    es_oferta = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    fecha_inicio_vigencia = models.DateField(blank=True, null=True)
    fecha_fin_vigencia = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    color = models.CharField(max_length=30)
    propiedad = models.CharField(max_length=50, blank=True)  # Ej: talla
    costo = models.DecimalField(max_digits=12, decimal_places=2)
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    numero_pagina = models.CharField(max_length=20, blank=True)
    temporada = models.CharField(max_length=30)
    oferta = models.BooleanField(default=False)
    admite_devolucion = models.BooleanField(default=True)
    stock_minimo = models.IntegerField(default=5)  # Nivel mínimo recomendado de stock
    proveedor = models.ForeignKey('proveedores.Proveedor', on_delete=models.PROTECT, related_name='productos')
    tienda = models.ForeignKey(Tienda, on_delete=models.PROTECT, related_name='productos')
    catalogo = models.ForeignKey(Catalogo, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(get_user_model(), related_name='productos_creados', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(get_user_model(), related_name='productos_actualizados', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.codigo} - {self.marca} {self.modelo}"
