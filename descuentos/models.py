from django.db import models

class TabuladorDescuento(models.Model):
    rango_min = models.DecimalField(max_digits=12, decimal_places=2)
    rango_max = models.DecimalField(max_digits=12, decimal_places=2)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.rango_min} - {self.rango_max}: {self.porcentaje}%"
