# Generated by Django 5.2 on 2025-05-01 02:53

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('productos', '0001_initial'),
        ('tiendas', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Traspaso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.PositiveIntegerField()),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('estado', models.CharField(default='pendiente', max_length=30)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='traspasos_creados', to=settings.AUTH_USER_MODEL)),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='traspasos', to='productos.producto')),
                ('tienda_destino', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='traspasos_entrada', to='tiendas.tienda')),
                ('tienda_origen', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='traspasos_salida', to='tiendas.tienda')),
            ],
        ),
        migrations.CreateModel(
            name='Inventario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad_actual', models.IntegerField(default=0)),
                ('fecha_registro', models.DateField(auto_now_add=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inventarios_creados', to=settings.AUTH_USER_MODEL)),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='inventarios', to='productos.producto')),
                ('tienda', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='inventarios', to='tiendas.tienda')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inventarios_actualizados', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('tienda', 'producto')},
            },
        ),
    ]
