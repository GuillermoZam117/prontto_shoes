"""
Utilidades para el sistema de pedidos avanzados
Sistema POS Pronto Shoes
"""

import os
import io
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.mail import send_mail

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from productos.models import Producto
from clientes.models import Cliente
from .models import OrdenCliente, ProductoCompartir


class GeneradorPDFCatalogo:
    """Generador de catálogos PDF personalizados para clientes"""
    
    def __init__(self, cliente: Cliente, productos: List[Producto] = None):
        self.cliente = cliente
        self.productos = productos or Producto.objects.filter(activo=True)
        self.buffer = io.BytesIO()
        
    def generar_catalogo_pdf(self) -> HttpResponse:
        """
        Genera un catálogo PDF personalizado para el cliente
        
        Returns:
            HttpResponse: Respuesta HTTP con el PDF generado
        """
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Elementos del documento
        story = []
        styles = getSampleStyleSheet()
        
        # Estilo personalizado para el título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#667eea')
        )
        
        # Estilo para subtítulos
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#2c3e50')
        )
        
        # Encabezado del catálogo
        story.append(Paragraph("CATÁLOGO PRONTO SHOES", title_style))
        story.append(Paragraph(f"Cliente: {self.cliente.nombre}", subtitle_style))
        story.append(Paragraph(f"Fecha: {timezone.now().strftime('%d/%m/%Y')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Información del cliente
        if hasattr(self.cliente, 'descuento_aplicado') and self.cliente.descuento_aplicado > 0:
            descuento_text = f"Descuento especial: {self.cliente.descuento_aplicado}%"
            story.append(Paragraph(descuento_text, styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Productos agrupados por categoría/proveedor
        productos_por_proveedor = {}
        for producto in self.productos:
            proveedor = getattr(producto, 'proveedor', 'Sin Proveedor')
            if proveedor not in productos_por_proveedor:
                productos_por_proveedor[proveedor] = []
            productos_por_proveedor[proveedor].append(producto)
        
        # Generar tabla de productos por proveedor
        for proveedor, productos_proveedor in productos_por_proveedor.items():
            story.append(Paragraph(f"Proveedor: {proveedor}", subtitle_style))
            
            # Datos de la tabla
            data = [['Código', 'Producto', 'Talla', 'Color', 'Precio']]
            
            for producto in productos_proveedor[:20]:  # Limitar a 20 productos por proveedor
                precio = getattr(producto, 'precio_venta', 0)
                if hasattr(self.cliente, 'descuento_aplicado') and self.cliente.descuento_aplicado > 0:
                    precio = precio * (1 - self.cliente.descuento_aplicado / 100)
                
                data.append([
                    producto.codigo or '',
                    producto.nombre[:30] + '...' if len(producto.nombre) > 30 else producto.nombre,
                    getattr(producto, 'talla', 'N/A'),
                    getattr(producto, 'color', 'N/A'),
                    f"${precio:.2f}"
                ])
            
            # Crear tabla
            table = Table(data, colWidths=[1*inch, 2.5*inch, 0.8*inch, 1*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 20))
        
        # Información de contacto
        story.append(Paragraph("Información de Contacto", subtitle_style))
        story.append(Paragraph("Pronto Shoes - Sistema POS", styles['Normal']))
        story.append(Paragraph("WhatsApp: +52 55 1234 5678", styles['Normal']))
        story.append(Paragraph("Email: ventas@prontoshoes.com", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Términos y condiciones
        story.append(Paragraph("Términos y Condiciones", subtitle_style))
        terminos = [
            "• Los precios están sujetos a cambios sin previo aviso",
            "• Descuentos aplicables según volumen de compra",
            "• Tiempo de entrega: 5-10 días hábiles",
            "• Devoluciones según política de proveedor"
        ]
        
        for termino in terminos:
            story.append(Paragraph(termino, styles['Normal']))
        
        # Construir PDF
        doc.build(story)
        
        # Preparar respuesta
        self.buffer.seek(0)
        response = HttpResponse(self.buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="catalogo_pronto_shoes_{self.cliente.id}_{timezone.now().strftime("%Y%m%d")}.pdf"'
        
        return response


class GestorCompartirRedes:
    """Gestor para compartir productos en redes sociales"""
    
    @staticmethod
    def generar_url_compartir(producto: Producto, cliente: Cliente, plataforma: str) -> str:
        """
        Genera URL para compartir producto en redes sociales
        
        Args:
            producto: Producto a compartir
            cliente: Cliente que comparte
            plataforma: Plataforma de destino (whatsapp, facebook, twitter, instagram)
            
        Returns:
            str: URL para compartir
        """
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        producto_url = f"{base_url}/productos/{producto.id}/"
        
        # Registrar el compartido
        ProductoCompartir.objects.create(
            producto=producto,
            cliente=cliente,
            plataforma=plataforma,
            url_compartida=producto_url
        )
        
        mensaje = f"¡Mira este producto de Pronto Shoes! {producto.nombre} - Código: {producto.codigo}"
        
        urls_plataformas = {
            'whatsapp': f"https://wa.me/?text={mensaje} {producto_url}",
            'facebook': f"https://www.facebook.com/sharer/sharer.php?u={producto_url}",
            'twitter': f"https://twitter.com/intent/tweet?text={mensaje}&url={producto_url}",
            'instagram': producto_url,  # Instagram no permite URLs directas
            'email': f"mailto:?subject=Producto Pronto Shoes&body={mensaje} {producto_url}",
            'copy': producto_url
        }
        
        return urls_plataformas.get(plataforma, producto_url)
    
    @staticmethod
    def obtener_estadisticas_cliente(cliente: Cliente) -> Dict:
        """
        Obtiene estadísticas de compartidos de un cliente
        
        Args:
            cliente: Cliente del que obtener estadísticas
            
        Returns:
            Dict: Estadísticas de compartidos
        """
        compartidos = ProductoCompartir.objects.filter(cliente=cliente)
        
        return {
            'total_compartidos': compartidos.count(),
            'total_clicks': sum(c.clicks_generados for c in compartidos),
            'plataformas_mas_usadas': list(
                compartidos.values('plataforma')
                .annotate(count=models.Count('id'))
                .order_by('-count')[:3]
            ),
            'productos_mas_compartidos': list(
                compartidos.values('producto__nombre', 'producto__codigo')
                .annotate(count=models.Count('id'))
                .order_by('-count')[:5]
            )
        }


class NotificadorAutomatico:
    """Clase para envío de notificaciones automáticas"""
    
    @staticmethod
    def notificar_cambio_estado_orden(orden: OrdenCliente, nuevo_estado: str):
        """
        Notifica al cliente sobre cambio de estado en su orden
        
        Args:
            orden: Orden que cambió de estado
            nuevo_estado: Nuevo estado de la orden
        """
        if not orden.cliente.email:
            return
        
        estados_messages = {
            'ACTIVO': 'Su orden está activa y recibiendo productos',
            'PENDIENTE': 'Su orden está pendiente de surtido',
            'VENTA': 'Su orden ha sido completada exitosamente',
            'CANCELADO': 'Su orden ha sido cancelada'
        }
        
        mensaje = estados_messages.get(nuevo_estado, 'Su orden ha sido actualizada')
        
        try:
            send_mail(
                subject=f'Actualización de Orden #{orden.numero_orden}',
                message=f"""
                Estimado {orden.cliente.nombre},
                
                {mensaje}.
                
                Detalles de la orden:
                - Número: {orden.numero_orden}
                - Estado: {orden.get_estado_display()}
                - Total productos: {orden.total_productos}
                - Monto: ${orden.monto_total}
                
                Puede revisar el estado completo en su portal de cliente.
                
                Saludos,
                Equipo Pronto Shoes
                """,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@prontoshoes.com'),
                recipient_list=[orden.cliente.email],
                fail_silently=True
            )
        except Exception as e:
            # Log error but don't fail
            pass
    
    @staticmethod
    def notificar_productos_listos_entrega(cliente: Cliente, productos_listos: List[Dict]):
        """
        Notifica al cliente sobre productos listos para entrega
        
        Args:
            cliente: Cliente a notificar
            productos_listos: Lista de productos listos
        """
        if not cliente.email or not productos_listos:
            return
        
        productos_texto = "\n".join([
            f"- {p['nombre']} (Código: {p['codigo']}) - Cantidad: {p['cantidad']}"
            for p in productos_listos
        ])
        
        try:
            send_mail(
                subject='Productos listos para entrega - Pronto Shoes',
                message=f"""
                Estimado {cliente.nombre},
                
                Los siguientes productos están listos para entrega:
                
                {productos_texto}
                
                Puede revisar los detalles completos en su portal de cliente o contactarnos para coordinar la entrega.
                
                Saludos,
                Equipo Pronto Shoes
                """,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@prontoshoes.com'),
                recipient_list=[cliente.email],
                fail_silently=True
            )
        except Exception as e:
            # Log error but don't fail
            pass


class AnalyticsPortalCliente:
    """Clase para analytics del portal de cliente"""
    
    @staticmethod
    def generar_metricas_cliente(cliente: Cliente) -> Dict:
        """
        Genera métricas completas de actividad del cliente
        
        Args:
            cliente: Cliente del que generar métricas
            
        Returns:
            Dict: Métricas del cliente
        """
        now = timezone.now()
        inicio_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        inicio_ano = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Órdenes
        ordenes = OrdenCliente.objects.filter(cliente=cliente)
        ordenes_mes = ordenes.filter(fecha_creacion__gte=inicio_mes)
        ordenes_ano = ordenes.filter(fecha_creacion__gte=inicio_ano)
        
        # Productos compartidos
        compartidos = ProductoCompartir.objects.filter(cliente=cliente)
        compartidos_mes = compartidos.filter(fecha_compartido__gte=inicio_mes)
        
        # Calcular tendencias
        meses_anteriores = inicio_mes - timedelta(days=30)
        ordenes_mes_anterior = ordenes.filter(
            fecha_creacion__gte=meses_anteriores,
            fecha_creacion__lt=inicio_mes
        )
        
        tendencia_ordenes = ordenes_mes.count() - ordenes_mes_anterior.count()
        
        return {
            'resumen_general': {
                'total_ordenes': ordenes.count(),
                'total_gastado': sum(orden.monto_total for orden in ordenes),
                'ordenes_activas': ordenes.filter(estado='ACTIVO').count(),
                'ordenes_completadas': ordenes.filter(estado='VENTA').count(),
            },
            'actividad_mes': {
                'ordenes_mes': ordenes_mes.count(),
                'monto_mes': sum(orden.monto_total for orden in ordenes_mes),
                'productos_compartidos': compartidos_mes.count(),
                'tendencia_ordenes': tendencia_ordenes,
            },
            'actividad_ano': {
                'ordenes_ano': ordenes_ano.count(),
                'monto_ano': sum(orden.monto_total for orden in ordenes_ano),
            },
            'estadisticas_compartir': GestorCompartirRedes.obtener_estadisticas_cliente(cliente),
            'ultima_actividad': {
                'ultima_orden': ordenes.order_by('-fecha_creacion').first(),
                'ultimo_compartido': compartidos.order_by('-fecha_compartido').first(),
            }
        }
