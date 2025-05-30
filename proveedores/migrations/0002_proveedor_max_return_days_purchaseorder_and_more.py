# Generated by Django 5.2 on 2025-05-19 23:54

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0002_catalogo_producto_catalogo"),
        ("proveedores", "0001_initial"),
        ("requisiciones", "0001_initial"),
        ("tiendas", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="proveedor",
            name="max_return_days",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.CreateModel(
            name="PurchaseOrder",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("pendiente", "Pendiente"),
                            ("enviado", "Enviado"),
                            ("recibido", "Recibido"),
                            ("cancelado", "Cancelado"),
                        ],
                        default="pendiente",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="purchase_orders_creadas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "proveedor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="purchase_orders",
                        to="proveedores.proveedor",
                    ),
                ),
                (
                    "tienda",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="purchase_orders",
                        to="tiendas.tienda",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PurchaseOrderItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("cantidad_solicitada", models.PositiveIntegerField()),
                ("cantidad_recibida", models.PositiveIntegerField(default=0)),
                (
                    "detalle_requisicion",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="purchase_order_items",
                        to="requisiciones.detallerequisicion",
                    ),
                ),
                (
                    "producto",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="purchase_order_items",
                        to="productos.producto",
                    ),
                ),
                (
                    "purchase_order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="proveedores.purchaseorder",
                    ),
                ),
            ],
        ),
    ]
