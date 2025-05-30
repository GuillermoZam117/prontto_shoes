# Generated by Django 5.2 on 2025-05-19 23:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReglaProgramaLealtad",
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
                (
                    "monto_compra_requerido",
                    models.DecimalField(decimal_places=2, max_digits=12, unique=True),
                ),
                ("puntos_otorgados", models.PositiveIntegerField()),
                ("activo", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddField(
            model_name="cliente",
            name="max_return_days",
            field=models.PositiveIntegerField(default=30),
        ),
        migrations.AddField(
            model_name="cliente",
            name="puntos_lealtad",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
