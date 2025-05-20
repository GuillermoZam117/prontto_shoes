from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Requisicion, DetalleRequisicion
from .serializers import RequisicionSerializer, DetalleRequisicionSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema

# Create your views here.

@extend_schema(tags=["Requisiciones"])
class RequisicionViewSet(viewsets.ModelViewSet):
    queryset = Requisicion.objects.all()
    serializer_class = RequisicionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cliente', 'fecha', 'estado']

    def get_queryset(self):
        # Allow admin/staff to see all requisitions
        if self.request.user and self.request.user.is_staff:
            return Requisicion.objects.all()
        # Allow only the client associated with the user to see their requisitions
        # This assumes a link between User and Cliente, e.g., request.user.cliente
        if self.request.user and hasattr(self.request.user, 'cliente'):
            return Requisicion.objects.filter(cliente=self.request.user.cliente)
        return Requisicion.objects.none() # No requisitions for unauthenticated or unlinked users

    def perform_create(self, serializer):
        # Associate the requisition with the client of the authenticated user
        # This assumes a link between User and Cliente
        if self.request.user and hasattr(self.request.user, 'cliente'):
            serializer.save(cliente=self.request.user.cliente)
        else:
            # Handle case where user is not linked to a client (should be prevented by permissions/validation)
            raise ValidationError("User is not associated with a client.")

    @action(detail=False, methods=['get'], url_path='my-requisitions')
    def my_requisitions(self, request):
        """
        Get requisitions for the authenticated client.
        """
        queryset = self.get_queryset() # Use the filtered queryset
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

@extend_schema(tags=["Requisiciones"])
class DetalleRequisicionViewSet(viewsets.ModelViewSet):
    queryset = DetalleRequisicion.objects.all()
    serializer_class = DetalleRequisicionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['requisicion', 'producto', 'cantidad']

@extend_schema(tags=["Reportes"])
class RequisicionesReporteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    """
    Devuelve un reporte de requisiciones realizadas, mostrando cliente, productos, cantidades, estado y fecha.
    """
    def get(self, request):
        from .models import Requisicion
        data = []
        requisiciones = Requisicion.objects.select_related('cliente').prefetch_related('detalles__producto').all()
        for req in requisiciones:
            detalles = []
            for det in req.detalles.all():
                detalles.append({
                    'producto_id': det.producto.id,
                    'producto_codigo': det.producto.codigo,
                    'producto_nombre': str(det.producto),
                    'cantidad': det.cantidad
                })
            data.append({
                'requisicion_id': req.id,
                'cliente_id': req.cliente.id,
                'cliente_nombre': req.cliente.nombre,
                'fecha': req.fecha,
                'estado': req.estado,
                'detalles': detalles
            })
        return Response(data)
