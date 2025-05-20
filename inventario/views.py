from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Inventario, Traspaso
from .serializers import InventarioSerializer, TraspasoSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.db.models import F # Import F object for atomic updates
from tiendas.models import Tienda
from productos.models import Producto

# Create your views here.

class InventarioViewSet(viewsets.ModelViewSet):
    queryset = Inventario.objects.all()
    serializer_class = InventarioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tienda', 'producto', 'cantidad_actual', 'fecha_registro']

class TraspasoViewSet(viewsets.ModelViewSet):
    queryset = Traspaso.objects.all()
    serializer_class = TraspasoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tienda_origen', 'tienda_destino', 'estado', 'fecha']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def confirmar_traspaso(self, request, pk=None):
        """
        Confirms a transfer, updating the inventory in origin and destination stores for each item.
        """
        traspaso = self.get_object()

        if traspaso.estado != 'pendiente':
            return Response({"error": f"El traspaso ya ha sido {traspaso.estado}."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            for item in traspaso.items.all():
                # Decrease inventory in origin store
                origin_inventory = Inventario.objects.select_for_update().get(
                    tienda=traspaso.tienda_origen,
                    producto=item.producto
                )
                if origin_inventory.cantidad_actual < item.cantidad:
                    raise ValidationError(f"Cantidad insuficiente para el producto {item.producto.codigo} en la tienda de origen.")
                origin_inventory.cantidad_actual = F('cantidad_actual') - item.cantidad
                origin_inventory.save()

                # Increase inventory in destination store
                destination_inventory, created = Inventario.objects.select_for_update().get_or_create(
                    tienda=traspaso.tienda_destino,
                    producto=item.producto,
                    defaults={'cantidad_actual': 0}
                )
                destination_inventory.cantidad_actual = F('cantidad_actual') + item.cantidad
                destination_inventory.save()

            # Update transfer status
            traspaso.estado = 'completado'
            traspaso.save()

        serializer = self.get_serializer(traspaso)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancelar_traspaso(self, request, pk=None):
        """
        Cancels a pending transfer.
        """
        traspaso = self.get_object()

        if traspaso.estado != 'pendiente':
            return Response({"error": f"El traspaso ya ha sido {traspaso.estado}. Solo se pueden cancelar traspasos pendientes."}, status=status.HTTP_400_BAD_REQUEST)

        traspaso.estado = 'cancelado'
        traspaso.save()

        serializer = self.get_serializer(traspaso)
        return Response(serializer.data)

class InventarioActualReporteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    """
    Devuelve un reporte del inventario actual agrupado por tienda y producto.
    """
    def get(self, request):
        data = []
        inventarios = Inventario.objects.select_related('tienda', 'producto').all()
        for inv in inventarios:
            data.append({
                'tienda_id': inv.tienda.id,
                'tienda_nombre': inv.tienda.nombre,
                'producto_id': inv.producto.id,
                'producto_codigo': inv.producto.codigo,
                'producto_nombre': str(inv.producto),
                'cantidad_actual': inv.cantidad_actual,
                'fecha_registro': inv.fecha_registro
            })
        return Response(data)
