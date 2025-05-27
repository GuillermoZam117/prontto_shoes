from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.auth.forms import UserCreationForm
from django import forms
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
import json
from datetime import datetime, timedelta

from .models import LogAuditoria, PerfilUsuario, ConfiguracionSistema
from .serializers import (LogAuditoriaSerializer, UsuarioSerializer, 
                         GrupoSerializer, PermisoSerializer, ConfiguracionSistemaSerializer)

User = get_user_model()

# Decorador para verificar si el usuario es administrador
def admin_required(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name='Administradores').exists())

# Función auxiliar para registrar actividad en auditoría
def registrar_auditoria(usuario, accion, descripcion, modelo_afectado=None, objeto_id=None, request=None):
    ip_address = None
    user_agent = ""
    
    if request:
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', 
                                    request.META.get('REMOTE_ADDR'))
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    LogAuditoria.objects.create(
        usuario=usuario,
        accion=accion,
        descripcion=descripcion,
        modelo_afectado=modelo_afectado,
        objeto_id=str(objeto_id) if objeto_id else '',
        ip_address=ip_address,
        user_agent=user_agent
    )

# ============== VISTAS PRINCIPALES ==============

@login_required
@user_passes_test(admin_required)
def dashboard_admin(request):
    """Dashboard principal de administración"""
    # Estadísticas generales
    total_usuarios = User.objects.count()
    usuarios_activos = User.objects.filter(is_active=True).count()
    usuarios_staff = User.objects.filter(is_staff=True).count()
    total_grupos = Group.objects.count()
    
    # Logs recientes
    logs_recientes = LogAuditoria.objects.select_related('usuario')[:10]
    
    # Actividad por día (últimos 7 días)
    fecha_inicio = timezone.now() - timedelta(days=7)
    actividad_diaria = (LogAuditoria.objects
                       .filter(fecha__gte=fecha_inicio)
                       .extra({'fecha_solo': "date(fecha)"})
                       .values('fecha_solo')
                       .annotate(total=Count('id'))
                       .order_by('fecha_solo'))
    
    context = {
        'total_usuarios': total_usuarios,
        'usuarios_activos': usuarios_activos,
        'usuarios_staff': usuarios_staff,
        'total_grupos': total_grupos,
        'logs_recientes': logs_recientes,
        'actividad_diaria': list(actividad_diaria),
    }
    
    return render(request, 'administracion/dashboard.html', context)

# ============== GESTIÓN DE USUARIOS ==============

@login_required
@user_passes_test(admin_required)
def lista_usuarios(request):
    """Lista todos los usuarios del sistema"""
    busqueda = request.GET.get('buscar', '')
    estado = request.GET.get('estado', '')
    grupo = request.GET.get('grupo', '')
    
    usuarios = User.objects.all().select_related('perfil').prefetch_related('groups')
    
    if busqueda:
        usuarios = usuarios.filter(
            Q(username__icontains=busqueda) |
            Q(first_name__icontains=busqueda) |
            Q(last_name__icontains=busqueda) |
            Q(email__icontains=busqueda)
        )
    
    if estado == 'activos':
        usuarios = usuarios.filter(is_active=True)
    elif estado == 'inactivos':
        usuarios = usuarios.filter(is_active=False)
    elif estado == 'staff':
        usuarios = usuarios.filter(is_staff=True)
    
    if grupo:
        usuarios = usuarios.filter(groups__id=grupo)
    
    paginator = Paginator(usuarios, 20)
    page = request.GET.get('page')
    usuarios_paginados = paginator.get_page(page)
    
    grupos = Group.objects.all()
    
    context = {
        'usuarios': usuarios_paginados,
        'grupos': grupos,
        'busqueda': busqueda,
        'estado': estado,
        'grupo': grupo,
    }
    
    return render(request, 'administracion/usuarios/lista.html', context)

class UsuarioForm(forms.ModelForm):
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label='Confirmar Contraseña', widget=forms.PasswordInput, required=False)
    grupos = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff']
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        
        return cleaned_data

@login_required
@user_passes_test(admin_required)
def crear_usuario(request):
    """Crear nuevo usuario"""
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            password = form.cleaned_data.get('password1')
            if password:
                usuario.set_password(password)
            usuario.save()
            
            # Asignar grupos
            grupos = form.cleaned_data.get('grupos')
            if grupos:
                usuario.groups.set(grupos)
            
            # Crear perfil
            PerfilUsuario.objects.get_or_create(usuario=usuario)
            
            # Registrar en auditoría
            registrar_auditoria(
                request.user, 'CREATE', 
                f'Usuario creado: {usuario.username}',
                'User', usuario.id, request
            )
            
            messages.success(request, f'Usuario {usuario.username} creado exitosamente.')
            return redirect('administracion:lista_usuarios')
    else:
        form = UsuarioForm()
    
    return render(request, 'administracion/usuarios/crear.html', {'form': form})

@login_required
@user_passes_test(admin_required)
def editar_usuario(request, usuario_id):
    """Editar usuario existente"""
    usuario = get_object_or_404(User, id=usuario_id)
    
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            usuario = form.save(commit=False)
            password = form.cleaned_data.get('password1')
            if password:
                usuario.set_password(password)
            usuario.save()
            
            # Asignar grupos
            grupos = form.cleaned_data.get('grupos')
            usuario.groups.set(grupos)
            
            # Registrar en auditoría
            registrar_auditoria(
                request.user, 'UPDATE', 
                f'Usuario editado: {usuario.username}',
                'User', usuario.id, request
            )
            
            messages.success(request, f'Usuario {usuario.username} actualizado exitosamente.')
            return redirect('administracion:lista_usuarios')
    else:
        form = UsuarioForm(instance=usuario)
        form.fields['grupos'].initial = usuario.groups.all()
    
    return render(request, 'administracion/usuarios/editar.html', {
        'form': form, 
        'usuario': usuario
    })

@login_required
@user_passes_test(admin_required)
@require_http_methods(["POST"])
def eliminar_usuario(request, usuario_id):
    """Eliminar usuario (marcar como inactivo)"""
    usuario = get_object_or_404(User, id=usuario_id)
    
    if usuario == request.user:
        messages.error(request, 'No puedes eliminar tu propia cuenta.')
        return redirect('administracion:lista_usuarios')
    
    if usuario.is_superuser:
        messages.error(request, 'No puedes eliminar una cuenta de superusuario.')
        return redirect('administracion:lista_usuarios')
    
    usuario.is_active = False
    usuario.save()
    
    # Registrar en auditoría
    registrar_auditoria(
        request.user, 'DELETE', 
        f'Usuario desactivado: {usuario.username}',
        'User', usuario.id, request
    )
    
    messages.success(request, f'Usuario {usuario.username} desactivado exitosamente.')
    return redirect('administracion:lista_usuarios')

@login_required
@user_passes_test(admin_required)
@require_http_methods(["POST"])
def cambiar_estado_usuario(request, usuario_id):
    """Cambiar estado activo/inactivo del usuario"""
    usuario = get_object_or_404(User, id=usuario_id)
    
    if usuario == request.user:
        messages.error(request, 'No puedes cambiar el estado de tu propia cuenta.')
        return redirect('administracion:lista_usuarios')
    
    usuario.is_active = not usuario.is_active
    usuario.save()
    
    estado = 'activado' if usuario.is_active else 'desactivado'
    
    # Registrar en auditoría
    registrar_auditoria(
        request.user, 'UPDATE', 
        f'Usuario {estado}: {usuario.username}',
        'User', usuario.id, request
    )
    
    messages.success(request, f'Usuario {usuario.username} {estado} exitosamente.')
    return redirect('administracion:lista_usuarios')

# ============== GESTIÓN DE GRUPOS ==============

@login_required
@user_passes_test(admin_required)
def lista_grupos(request):
    """Lista todos los grupos del sistema"""
    grupos = Group.objects.annotate(
        usuarios_count=Count('user'),
        permisos_count=Count('permissions')
    ).all()
    
    return render(request, 'administracion/grupos/lista.html', {'grupos': grupos})

class GrupoForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = Group
        fields = ['name', 'permissions']

@login_required
@user_passes_test(admin_required)
def crear_grupo(request):
    """Crear nuevo grupo"""
    if request.method == 'POST':
        form = GrupoForm(request.POST)
        if form.is_valid():
            grupo = form.save()
            
            # Registrar en auditoría
            registrar_auditoria(
                request.user, 'CREATE', 
                f'Grupo creado: {grupo.name}',
                'Group', grupo.id, request
            )
            
            messages.success(request, f'Grupo {grupo.name} creado exitosamente.')
            return redirect('administracion:lista_grupos')
    else:
        form = GrupoForm()
    
    return render(request, 'administracion/grupos/crear.html', {'form': form})

@login_required
@user_passes_test(admin_required)
def editar_grupo(request, grupo_id):
    """Editar grupo existente"""
    grupo = get_object_or_404(Group, id=grupo_id)
    
    if request.method == 'POST':
        form = GrupoForm(request.POST, instance=grupo)
        if form.is_valid():
            grupo = form.save()
            
            # Registrar en auditoría
            registrar_auditoria(
                request.user, 'UPDATE', 
                f'Grupo editado: {grupo.name}',
                'Group', grupo.id, request
            )
            
            messages.success(request, f'Grupo {grupo.name} actualizado exitosamente.')
            return redirect('administracion:lista_grupos')
    else:
        form = GrupoForm(instance=grupo)
    
    return render(request, 'administracion/grupos/editar.html', {
        'form': form, 
        'grupo': grupo
    })

@login_required
@user_passes_test(admin_required)
@require_http_methods(["POST"])
def eliminar_grupo(request, grupo_id):
    """Eliminar grupo"""
    grupo = get_object_or_404(Group, id=grupo_id)
    
    # Verificar si el grupo tiene usuarios asignados
    if grupo.user_set.exists():
        messages.error(request, f'No se puede eliminar el grupo {grupo.name} porque tiene usuarios asignados.')
        return redirect('administracion:lista_grupos')
    
    nombre_grupo = grupo.name
    grupo.delete()
    
    # Registrar en auditoría
    registrar_auditoria(
        request.user, 'DELETE', 
        f'Grupo eliminado: {nombre_grupo}',
        'Group', grupo_id, request
    )
    
    messages.success(request, f'Grupo {nombre_grupo} eliminado exitosamente.')
    return redirect('administracion:lista_grupos')

# ============== GESTIÓN DE PERMISOS ==============

@login_required
@user_passes_test(admin_required)
def gestionar_permisos_usuario(request, usuario_id):
    """Gestionar permisos específicos de un usuario"""
    usuario = get_object_or_404(User, id=usuario_id)
    permisos_disponibles = Permission.objects.all().select_related('content_type')
    permisos_usuario = usuario.user_permissions.all()
    permisos_por_grupo = Permission.objects.filter(group__user=usuario).distinct()
    
    if request.method == 'POST':
        permisos_seleccionados = request.POST.getlist('permisos')
        permisos_objects = Permission.objects.filter(id__in=permisos_seleccionados)
        usuario.user_permissions.set(permisos_objects)
        
        # Registrar en auditoría
        registrar_auditoria(
            request.user, 'UPDATE', 
            f'Permisos actualizados para usuario: {usuario.username}',
            'User', usuario.id, request
        )
        
        messages.success(request, f'Permisos de {usuario.username} actualizados exitosamente.')
        return redirect('administracion:lista_usuarios')
    
    context = {
        'usuario': usuario,
        'permisos_disponibles': permisos_disponibles,
        'permisos_usuario': permisos_usuario,
        'permisos_por_grupo': permisos_por_grupo,
    }
    
    return render(request, 'administracion/usuarios/permisos.html', context)

# ============== AUDITORÍA Y LOGS ==============

@login_required
@user_passes_test(admin_required)
def auditoria_dashboard(request):
    """Dashboard de auditoría con métricas"""
    # Estadísticas de los últimos 30 días
    fecha_inicio = timezone.now() - timedelta(days=30)
    
    total_eventos = LogAuditoria.objects.filter(fecha__gte=fecha_inicio).count()
    eventos_por_accion = (LogAuditoria.objects
                         .filter(fecha__gte=fecha_inicio)
                         .values('accion')
                         .annotate(total=Count('id'))
                         .order_by('-total')[:10])
    
    usuarios_mas_activos = (LogAuditoria.objects
                          .filter(fecha__gte=fecha_inicio)
                          .exclude(usuario__isnull=True)
                          .values('usuario__username')
                          .annotate(total=Count('id'))
                          .order_by('-total')[:10])
    
    # Actividad por hora del día
    actividad_por_hora = (LogAuditoria.objects
                         .filter(fecha__gte=fecha_inicio)
                         .extra({'hora': "extract(hour from fecha)"})
                         .values('hora')
                         .annotate(total=Count('id'))
                         .order_by('hora'))
    
    context = {
        'total_eventos': total_eventos,
        'eventos_por_accion': list(eventos_por_accion),
        'usuarios_mas_activos': list(usuarios_mas_activos),
        'actividad_por_hora': list(actividad_por_hora),
    }
    
    return render(request, 'administracion/auditoria/dashboard.html', context)

@login_required
@user_passes_test(admin_required)
def logs_auditoria(request):
    """Listado de logs de auditoría con filtros"""
    usuario_filtro = request.GET.get('usuario', '')
    accion_filtro = request.GET.get('accion', '')
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    busqueda = request.GET.get('buscar', '')
    
    logs = LogAuditoria.objects.select_related('usuario').all()
    
    if usuario_filtro:
        logs = logs.filter(usuario__id=usuario_filtro)
    
    if accion_filtro:
        logs = logs.filter(accion=accion_filtro)
    
    if fecha_inicio:
        logs = logs.filter(fecha__date__gte=fecha_inicio)
    
    if fecha_fin:
        logs = logs.filter(fecha__date__lte=fecha_fin)
    
    if busqueda:
        logs = logs.filter(
            Q(descripcion__icontains=busqueda) |
            Q(modelo_afectado__icontains=busqueda) |
            Q(objeto_id__icontains=busqueda)
        )
    
    paginator = Paginator(logs, 50)
    page = request.GET.get('page')
    logs_paginados = paginator.get_page(page)
    
    usuarios = User.objects.all()
    acciones = LogAuditoria.ACCION_CHOICES
    
    context = {
        'logs': logs_paginados,
        'usuarios': usuarios,
        'acciones': acciones,
        'usuario_filtro': usuario_filtro,
        'accion_filtro': accion_filtro,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'busqueda': busqueda,
    }
    
    return render(request, 'administracion/auditoria/logs.html', context)

@login_required
@user_passes_test(admin_required)
def reporte_auditoria(request):
    """Generar reporte de auditoría"""
    formato = request.GET.get('formato', 'html')
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    
    logs = LogAuditoria.objects.select_related('usuario').all()
    
    if fecha_inicio:
        logs = logs.filter(fecha__date__gte=fecha_inicio)
    
    if fecha_fin:
        logs = logs.filter(fecha__date__lte=fecha_fin)
    
    if formato == 'json':
        data = []
        for log in logs:
            data.append({
                'fecha': log.fecha.isoformat(),
                'usuario': log.usuario.username if log.usuario else None,
                'accion': log.get_accion_display(),
                'descripcion': log.descripcion,
                'modelo_afectado': log.modelo_afectado,
                'objeto_id': log.objeto_id,
                'ip_address': log.ip_address,
            })
        
        response = HttpResponse(
            json.dumps(data, indent=2, ensure_ascii=False),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="auditoria_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
        return response
    
    context = {
        'logs': logs,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'total_logs': logs.count(),
    }
    
    return render(request, 'administracion/auditoria/reporte.html', context)

# ============== CONFIGURACIÓN DEL SISTEMA ==============

@login_required
@user_passes_test(admin_required)
def configuracion_sistema(request):
    """Gestión de configuraciones del sistema"""
    configuraciones = ConfiguracionSistema.objects.all().order_by('clave')
    
    if request.method == 'POST':
        for config in configuraciones:
            nuevo_valor = request.POST.get(f'config_{config.id}')
            if nuevo_valor is not None and nuevo_valor != config.valor:
                valor_anterior = config.valor
                config.valor = nuevo_valor
                config.modificado_por = request.user
                config.save()
                
                # Registrar en auditoría
                registrar_auditoria(
                    request.user, 'CONFIG', 
                    f'Configuración {config.clave} cambiada de "{valor_anterior}" a "{nuevo_valor}"',
                    'ConfiguracionSistema', config.id, request
                )
        
        messages.success(request, 'Configuraciones actualizadas exitosamente.')
        return redirect('administracion:configuracion_sistema')
    
    return render(request, 'administracion/configuracion/sistema.html', {
        'configuraciones': configuraciones
    })

@login_required
@user_passes_test(admin_required)
def backup_sistema(request):
    """Generar respaldo del sistema"""
    if request.method == 'POST':
        # Aquí iría la lógica para generar el respaldo
        # Por ahora solo registramos la acción
        
        registrar_auditoria(
            request.user, 'BACKUP', 
            'Respaldo del sistema generado',
            'Sistema', None, request
        )
        
        messages.success(request, 'Respaldo del sistema generado exitosamente.')
        return redirect('administracion:configuracion_sistema')
    
    return render(request, 'administracion/configuracion/backup.html')

# ============== APIs PARA HTMX/AJAX ==============

@login_required
@user_passes_test(admin_required)
def api_buscar_usuarios(request):
    """API para búsqueda AJAX de usuarios"""
    termino = request.GET.get('q', '')
    usuarios = User.objects.filter(
        Q(username__icontains=termino) |
        Q(first_name__icontains=termino) |
        Q(last_name__icontains=termino)
    )[:10]
    
    resultados = [{
        'id': u.id,
        'username': u.username,
        'nombre_completo': f"{u.first_name} {u.last_name}".strip(),
        'email': u.email,
        'is_active': u.is_active
    } for u in usuarios]
    
    return JsonResponse({'usuarios': resultados})

@login_required
@user_passes_test(admin_required)
def api_filtrar_logs(request):
    """API para filtrar logs de auditoría en tiempo real"""
    accion = request.GET.get('accion', '')
    usuario_id = request.GET.get('usuario_id', '')
    
    logs = LogAuditoria.objects.select_related('usuario')
    
    if accion:
        logs = logs.filter(accion=accion)
    
    if usuario_id:
        logs = logs.filter(usuario_id=usuario_id)
    
    logs = logs[:20]  # Limitar a 20 resultados
    
    resultados = [{
        'id': log.id,
        'fecha': log.fecha.strftime('%Y-%m-%d %H:%M:%S'),
        'usuario': log.usuario.username if log.usuario else 'Sistema',
        'accion': log.get_accion_display(),
        'descripcion': log.descripcion,
        'ip_address': log.ip_address or '',
    } for log in logs]
    
    return JsonResponse({'logs': resultados})

# ============== API REST VIEWSETS ==============

class LogAuditoriaViewSet(viewsets.ModelViewSet):
    queryset = LogAuditoria.objects.all()
    serializer_class = LogAuditoriaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['usuario', 'accion', 'fecha']

class LogsAuditoriaReporteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogAuditoriaSerializer  # Add this for DRF Spectacular
    """
    Devuelve un reporte de logs de auditoría, mostrando usuario, acción, fecha y descripción.
    """
    def get(self, request):
        from .models import LogAuditoria
        data = []
        logs = LogAuditoria.objects.select_related('usuario').all().order_by('-fecha')
        for log in logs:
            data.append({
                'id': log.id,
                'usuario_id': log.usuario.id if log.usuario else None,
                'usuario_username': log.usuario.username if log.usuario else None,
                'accion': log.accion,
                'accion_display': log.get_accion_display(),
                'fecha': log.fecha,
                'descripcion': log.descripcion,
                'modelo_afectado': log.modelo_afectado,
                'objeto_id': log.objeto_id,
                'ip_address': log.ip_address,
            })
        return Response(data)
