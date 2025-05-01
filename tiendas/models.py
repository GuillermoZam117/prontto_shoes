from django.db import models
from django.contrib.auth import get_user_model

class Tienda(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    direccion = models.CharField(max_length=255)
    contacto = models.CharField(max_length=100, blank=True)
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(get_user_model(), related_name='tiendas_creadas', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(get_user_model(), related_name='tiendas_actualizadas', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nombre
