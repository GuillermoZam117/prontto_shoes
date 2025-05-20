from rest_framework import serializers
from .models import Requisicion, DetalleRequisicion
from productos.models import Producto, Catalogo
from rest_framework.exceptions import ValidationError
from django.db import transaction

class DetalleRequisicionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleRequisicion
        fields = '__all__'

class RequisicionSerializer(serializers.ModelSerializer):
    detalles = DetalleRequisicionSerializer(many=True)

    class Meta:
        model = Requisicion
        fields = '__all__'
        read_only_fields = ('estado',)

    def create(self, validated_data):
        with transaction.atomic():
            detalles_data = validated_data.pop('detalles')
            requisicion = Requisicion.objects.create(**validated_data)
            # Set initial status
            requisicion.estado = 'pendiente'
            requisicion.save()

            for detalle_data in detalles_data:
                producto = detalle_data['producto']
                cantidad = detalle_data['cantidad']

                # Validate product is in a vigente catalog
                if not Catalogo.objects.filter(productos=producto, activo=True).exists():
                     raise ValidationError(f"Producto {producto.codigo} no está en un catálogo vigente.")

                # Validate no duplicate product in the same requisition (handled by serializer.save() on update)
                # For creation, we need to check across existing requisitions for the same client and product
                # This validation requires client information which is in validated_data
                cliente = validated_data['cliente']
                if Requisicion.objects.filter(cliente=cliente, detalles__producto=producto, estado__in=['pendiente', 'procesada']).exists():
                     raise ValidationError(f"Ya existe un pedido pendiente o en proceso para el cliente {cliente.nombre} con el producto {producto.codigo}.")

                DetalleRequisicion.objects.create(requisicion=requisicion, **detalle_data)

            return requisicion

    def update(self, instance, validated_data):
        # Handle updates to details if necessary, similar to create
        # For simplicity, this example focuses on create
        raise serializers.ValidationError("Updates to requisitions are not allowed via this endpoint.")
