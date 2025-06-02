# Generated manually for advanced order system implementation
# Fecha: 28 de Mayo, 2025
# Autor: Sistema POS Pronto Shoes - Transformación a Pedidos Avanzados

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('ventas', '0001_initial'),
    ]

    operations = [
        # Extensión de tabla Pedido con campos avanzados
        migrations.AddField(
            model_name='pedido',
            name='es_pedido_padre',
            field=models.BooleanField(default=False, help_text='Indica si este pedido es padre de otros pedidos parciales'),
        ),
        migrations.AddField(
            model_name='pedido',
            name='pedido_padre',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pedidos_hijos', to='ventas.pedido', help_text='Referencia al pedido padre si este es un pedido parcial'),
        ),
        migrations.AddField(
            model_name='pedido',
            name='numero_ticket',
            field=models.CharField(blank=True, max_length=50, unique=True, null=True, help_text='Número único de ticket para entregas parciales'),
        ),
        migrations.AddField(
            model_name='pedido',
            name='porcentaje_completado',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5, help_text='Porcentaje de completitud del pedido (0-100)'),
        ),
        migrations.AddField(
            model_name='pedido',
            name='fecha_conversion_venta',
            field=models.DateTimeField(blank=True, null=True, help_text='Fecha cuando el pedido se convirtió en venta'),
        ),
        migrations.AddField(
            model_name='pedido',
            name='permite_entrega_parcial',
            field=models.BooleanField(default=True, help_text='Permite entregas parciales de este pedido'),
        ),
    ]
