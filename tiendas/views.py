from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Tienda
from .serializers import TiendaSerializer

class TiendaViewSet(viewsets.ModelViewSet):
    queryset = Tienda.objects.all()
    serializer_class = TiendaSerializer
    permission_classes = [IsAuthenticated]

@login_required
def tienda_list(request):
    """Vista para listar todas las tiendas"""
    tiendas = Tienda.objects.all().order_by('nombre')
    return render(request, 'tiendas/tienda_list.html', {
        'tiendas': tiendas,
    })

@login_required
def tienda_detail(request, pk):
    """Vista para ver detalle de una tienda"""
    tienda = get_object_or_404(Tienda, pk=pk)
    return render(request, 'tiendas/tienda_detail.html', {
        'tienda': tienda,
    })

@login_required
def tienda_create(request):
    """Vista para crear una nueva tienda"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        direccion = request.POST.get('direccion')
        contacto = request.POST.get('contacto')
        activa = request.POST.get('activa') == 'on'
        
        if nombre and direccion:
            tienda = Tienda.objects.create(
                nombre=nombre,
                direccion=direccion,
                contacto=contacto,
                activa=activa,
                created_by=request.user,
                updated_by=request.user
            )
            messages.success(request, f'Tienda {tienda.nombre} creada con éxito')
            return redirect('tiendas:lista')
        else:
            messages.error(request, 'Por favor completa todos los campos requeridos')
    
    return render(request, 'tiendas/tienda_form.html')

@login_required
def tienda_edit(request, pk):
    """Vista para editar una tienda existente"""
    tienda = get_object_or_404(Tienda, pk=pk)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        direccion = request.POST.get('direccion')
        contacto = request.POST.get('contacto')
        activa = request.POST.get('activa') == 'on'
        
        if nombre and direccion:
            tienda.nombre = nombre
            tienda.direccion = direccion
            tienda.contacto = contacto
            tienda.activa = activa
            tienda.updated_by = request.user
            tienda.save()
            
            messages.success(request, f'Tienda {tienda.nombre} actualizada con éxito')
            return redirect('tiendas:detalle', pk=tienda.pk)
        else:
            messages.error(request, 'Por favor completa todos los campos requeridos')
    
    return render(request, 'tiendas/tienda_form.html', {
        'tienda': tienda,
        'is_edit': True
    })

@login_required
def tienda_delete(request, pk):
    """Vista para eliminar una tienda"""
    tienda = get_object_or_404(Tienda, pk=pk)
    
    if request.method == 'POST':
        nombre = tienda.nombre
        tienda.delete()
        messages.success(request, f'Tienda {nombre} eliminada con éxito')
        return redirect('tiendas:lista')
    
    return render(request, 'tiendas/tienda_confirm_delete.html', {
        'tienda': tienda
    })

@login_required
def tienda_sync_dashboard(request):
    """Vista que redirige al dashboard de sincronización de la tienda"""
    return redirect('sincronizacion_dashboard')
