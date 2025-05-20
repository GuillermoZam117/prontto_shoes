from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import TabuladorDescuento
from .serializers import TabuladorDescuentoSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Avg, Count, Sum, F
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from clientes.models import Cliente, DescuentoCliente

# Frontend views for discount table
@login_required
def tabulador_list(request):
    """Vista para listar los rangos de descuento en el tabulador"""
    descuentos = TabuladorDescuento.objects.all().order_by('rango_min')
    
    # Calculate metrics for summary cards
    promedio_descuento = descuentos.aggregate(avg=Avg('porcentaje'))['avg'] if descuentos else 0
    
    context = {
        'descuentos': descuentos,
        'promedio_descuento': promedio_descuento,
    }
    
    return render(request, 'descuentos/tabulador_list.html', context)

@login_required
def tabulador_detail(request, pk):
    """Vista de detalle de un rango de descuento"""
    descuento = get_object_or_404(TabuladorDescuento, pk=pk)
    
    # Get all ranges for context
    rangos_ordenados = TabuladorDescuento.objects.all().order_by('rango_min')
    
    # Prepare data for graphical representation
    rangos_completos = []
    max_rango = TabuladorDescuento.objects.aggregate(max=Sum('rango_max'))['max'] or 50000
    
    for rango in rangos_ordenados:
        porcentaje_grafico = ((rango.rango_max - rango.rango_min) / max_rango) * 100
        rangos_completos.append({
            'id': rango.id,
            'rango_min': rango.rango_min,
            'rango_max': rango.rango_max,
            'porcentaje': rango.porcentaje,
            'porcentaje_grafico': min(porcentaje_grafico, 40)  # Cap at 40% to ensure all are visible
        })
    
    # Calculate examples for this discount
    porcentaje_decimal = descuento.porcentaje / 100
    ejemplo_min_descuento = descuento.rango_min * porcentaje_decimal
    ejemplo_min_final = descuento.rango_min - ejemplo_min_descuento
    
    ejemplo_promedio = (descuento.rango_min + descuento.rango_max) / 2
    ejemplo_promedio_descuento = ejemplo_promedio * porcentaje_decimal
    ejemplo_promedio_final = ejemplo_promedio - ejemplo_promedio_descuento
    
    ejemplo_max_descuento = descuento.rango_max * porcentaje_decimal
    ejemplo_max_final = descuento.rango_max - ejemplo_max_descuento
    
    # Get client statistics for this range
    # Count clients in this range and total discounted amount
    clientes_en_rango = Cliente.objects.filter(
        monto_acumulado__gte=descuento.rango_min,
        monto_acumulado__lt=descuento.rango_max
    ).count()
    
    # Calculate total saved by clients in this range (from discounts applied)
    descuentos_aplicados = DescuentoCliente.objects.filter(
        cliente__monto_acumulado__gte=descuento.rango_min,
        cliente__monto_acumulado__lt=descuento.rango_max
    )
    total_ahorrado = descuentos_aplicados.aggregate(total=Sum('monto'))['total'] or 0
    
    context = {
        'descuento': descuento,
        'rangos_ordenados': rangos_ordenados,
        'rangos_completos': rangos_completos,
        'ejemplo_min_descuento': ejemplo_min_descuento,
        'ejemplo_min_final': ejemplo_min_final,
        'ejemplo_promedio': ejemplo_promedio,
        'ejemplo_promedio_descuento': ejemplo_promedio_descuento,
        'ejemplo_promedio_final': ejemplo_promedio_final,
        'ejemplo_max_descuento': ejemplo_max_descuento,
        'ejemplo_max_final': ejemplo_max_final,
        'clientes_en_rango': clientes_en_rango,
        'total_ahorrado': total_ahorrado,
    }
    
    return render(request, 'descuentos/tabulador_detail.html', context)

@login_required
def tabulador_create(request):
    """Vista para crear un nuevo rango de descuento"""
    rangos_existentes = TabuladorDescuento.objects.all().order_by('rango_min')
    
    if request.method == 'POST':
        try:
            # Get form data
            rango_min = float(request.POST.get('rango_min', 0))
            rango_max = float(request.POST.get('rango_max', 0))
            porcentaje = float(request.POST.get('porcentaje', 0))
            
            # Validate
            if rango_min >= rango_max:
                messages.error(request, "El rango mínimo debe ser menor que el rango máximo.")
                return render(request, 'descuentos/tabulador_form.html', {
                    'rangos_existentes': rangos_existentes,
                    'error_message': "El rango mínimo debe ser menor que el rango máximo."
                })
            
            # Check for overlap with existing ranges
            overlapping = TabuladorDescuento.objects.filter(
                rango_min__lt=rango_max,
                rango_max__gt=rango_min
            ).exists()
            
            if overlapping:
                messages.error(request, "Este rango se solapa con rangos existentes. Por favor, revise los valores.")
                return render(request, 'descuentos/tabulador_form.html', {
                    'rangos_existentes': rangos_existentes,
                    'error_message': "Este rango se solapa con rangos existentes. Por favor, revise los valores."
                })
            
            # Create new discount range
            descuento = TabuladorDescuento(
                rango_min=rango_min,
                rango_max=rango_max,
                porcentaje=porcentaje
            )
            descuento.save()
            
            messages.success(request, "Rango de descuento creado exitosamente.")
            return redirect('descuentos:detalle', pk=descuento.pk)
            
        except ValueError:
            messages.error(request, "Valores no válidos. Por favor, verifique los datos ingresados.")
    
    context = {
        'rangos_existentes': rangos_existentes,
    }
    
    return render(request, 'descuentos/tabulador_form.html', context)

@login_required
def tabulador_edit(request, pk):
    """Vista para editar un rango de descuento existente"""
    descuento = get_object_or_404(TabuladorDescuento, pk=pk)
    rangos_existentes = TabuladorDescuento.objects.all().order_by('rango_min')
    
    if request.method == 'POST':
        try:
            # Get form data
            rango_min = float(request.POST.get('rango_min', 0))
            rango_max = float(request.POST.get('rango_max', 0))
            porcentaje = float(request.POST.get('porcentaje', 0))
            
            # Validate
            if rango_min >= rango_max:
                messages.error(request, "El rango mínimo debe ser menor que el rango máximo.")
                return render(request, 'descuentos/tabulador_form.html', {
                    'descuento': descuento,
                    'rangos_existentes': rangos_existentes,
                    'is_edit': True,
                    'error_message': "El rango mínimo debe ser menor que el rango máximo."
                })
            
            # Check for overlap with existing ranges (excluding this one)
            overlapping = TabuladorDescuento.objects.filter(
                rango_min__lt=rango_max,
                rango_max__gt=rango_min
            ).exclude(pk=pk).exists()
            
            if overlapping:
                messages.error(request, "Este rango se solapa con otros rangos existentes. Por favor, revise los valores.")
                return render(request, 'descuentos/tabulador_form.html', {
                    'descuento': descuento,
                    'rangos_existentes': rangos_existentes,
                    'is_edit': True,
                    'error_message': "Este rango se solapa con otros rangos existentes. Por favor, revise los valores."
                })
            
            # Update discount range
            descuento.rango_min = rango_min
            descuento.rango_max = rango_max
            descuento.porcentaje = porcentaje
            descuento.save()
            
            messages.success(request, "Rango de descuento actualizado exitosamente.")
            return redirect('descuentos:detalle', pk=descuento.pk)
            
        except ValueError:
            messages.error(request, "Valores no válidos. Por favor, verifique los datos ingresados.")
    
    context = {
        'descuento': descuento,
        'rangos_existentes': rangos_existentes,
        'is_edit': True,
    }
    
    return render(request, 'descuentos/tabulador_form.html', context)

# API ViewSets
class TabuladorDescuentoViewSet(viewsets.ModelViewSet):
    queryset = TabuladorDescuento.objects.all()
    serializer_class = TabuladorDescuentoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['rango_min', 'rango_max', 'porcentaje']

class DescuentosReporteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    """
    Devuelve un reporte del tabulador de descuentos, mostrando rango mínimo, rango máximo y porcentaje.
    """
    def get(self, request):
        from .models import TabuladorDescuento
        data = []
        descuentos = TabuladorDescuento.objects.all()
        for desc in descuentos:
            data.append({
                'id': desc.id,
                'rango_min': desc.rango_min,
                'rango_max': desc.rango_max,
                'porcentaje': desc.porcentaje
            })
        return Response(data)

# Create your views here.
