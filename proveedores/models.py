from django.db import models
from tiendas.models import Tienda
from django.contrib.auth import get_user_model

class Proveedor(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    contacto = models.CharField(max_length=100, blank=True)
    requiere_anticipo = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(get_user_model(), related_name='proveedores_creados', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(get_user_model(), related_name='proveedores_actualizados', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nombre
