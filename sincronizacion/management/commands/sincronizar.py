import time
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db.models import Q
from sincronizacion.models import ColaSincronizacion, RegistroSincronizacion, EstadoSincronizacion
from sincronizacion.tasks import procesar_cola_sincronizacion, iniciar_sincronizacion_completa
from tiendas.models import Tienda

class Command(BaseCommand):
    help = "Procesa la cola de sincronización pendiente o inicia una sincronización completa"

    def add_arguments(self, parser):
        parser.add_argument(
            '--tienda',
            type=int,
            help='ID de la tienda para sincronizar (opcional)'
        )
        
        parser.add_argument(
            '--operacion',
            type=str,
            help='ID de la operación específica a procesar (opcional)'
        )
        
        parser.add_argument(
            '--max',
            type=int,
            default=100,
            help='Número máximo de operaciones a procesar (predeterminado: 100)'
        )
        
        parser.add_argument(
            '--completa',
            action='store_true',
            help='Realizar sincronización completa (crea un registro)'
        )
        
        parser.add_argument(
            '--simular',
            action='store_true',
            help='Modo simulación (no realiza cambios reales)'
        )
        
        parser.add_argument(
            '--continuo',
            action='store_true',
            help='Ejecutar en modo continuo, verificando periódicamente'
        )
        
        parser.add_argument(
            '--intervalo',
            type=int,
            default=60,
            help='Intervalo en segundos para modo continuo (predeterminado: 60)'
        )

    def handle(self, *args, **options):
        tienda_id = options['tienda']
        operacion_id = options['operacion']
        max_items = options['max']
        modo_completo = options['completa']
        simular = options['simular']
        continuo = options['continuo']
        intervalo = options['intervalo']
        
        if simular:
            self.stdout.write(self.style.WARNING("Ejecutando en modo simulación - no se realizarán cambios reales"))
        
        if continuo:
            self.stdout.write(self.style.SUCCESS(f"Iniciando modo continuo con intervalo de {intervalo} segundos"))
            self.ejecutar_modo_continuo(tienda_id, max_items, simular, intervalo)
        elif modo_completo:
            self.ejecutar_sincronizacion_completa(tienda_id, simular)
        else:
            self.ejecutar_sincronizacion_parcial(tienda_id, operacion_id, max_items, simular)

    def ejecutar_sincronizacion_parcial(self, tienda_id, operacion_id, max_items, simular):
        """Ejecuta una sincronización parcial (solo cola pendiente)"""
        self.stdout.write("Procesando operaciones pendientes...")
        
        inicio = timezone.now()
        exitosas, fallidas, conflictos = procesar_cola_sincronizacion(
            operacion_id=operacion_id, 
            tienda_id=tienda_id,
            max_items=max_items,
            simular=simular
        )
        fin = timezone.now()
        
        tiempo = (fin - inicio).total_seconds()
        total = exitosas + fallidas + conflictos
        
        self.stdout.write(self.style.SUCCESS(
            f"Sincronización completada en {tiempo:.2f} segundos. "
            f"Total: {total}, Exitosas: {exitosas}, Fallidas: {fallidas}, Conflictos: {conflictos}"
        ))

    def ejecutar_sincronizacion_completa(self, tienda_id, simular):
        """Ejecuta una sincronización completa (crea un registro de seguimiento)"""
        if not tienda_id:
            self.stdout.write(self.style.ERROR("Debe especificar una tienda para sincronización completa"))
            return
        
        try:
            tienda = Tienda.objects.get(pk=tienda_id)
        except Tienda.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"No se encontró la tienda con ID {tienda_id}"))
            return
        
        self.stdout.write(f"Iniciando sincronización completa para tienda: {tienda.nombre}")
        
        if simular:
            # En modo simulación, no creamos registro real
            self.ejecutar_sincronizacion_parcial(tienda_id, None, 100, simular)
            return
        
        registro_id = iniciar_sincronizacion_completa(tienda_id)
        
        if registro_id:
            registro = RegistroSincronizacion.objects.get(pk=registro_id)
            self.stdout.write(self.style.SUCCESS(
                f"Sincronización completada para {tienda.nombre}. "
                f"Exitosas: {registro.operaciones_exitosas}, "
                f"Fallidas: {registro.operaciones_fallidas}, "
                f"Conflictos: {registro.operaciones_con_conflicto}"
            ))
        else:
            self.stdout.write(self.style.ERROR("Error al iniciar sincronización completa"))

    def ejecutar_modo_continuo(self, tienda_id, max_items, simular, intervalo):
        """Ejecuta en modo continuo, verificando periódicamente"""
        try:
            while True:
                inicio = timezone.now()
                
                # Contar operaciones pendientes
                filtro = Q(estado=EstadoSincronizacion.PENDIENTE)
                if tienda_id:
                    filtro &= Q(tienda_origen_id=tienda_id)
                pendientes = ColaSincronizacion.objects.filter(filtro).count()
                
                if pendientes > 0:
                    self.stdout.write(f"{inicio.strftime('%H:%M:%S')} - {pendientes} operaciones pendientes")
                    exitosas, fallidas, conflictos = procesar_cola_sincronizacion(
                        tienda_id=tienda_id,
                        max_items=max_items,
                        simular=simular
                    )
                    
                    self.stdout.write(self.style.SUCCESS(
                        f"Procesadas: {exitosas + fallidas + conflictos}, "
                        f"Exitosas: {exitosas}, Fallidas: {fallidas}, Conflictos: {conflictos}"
                    ))
                else:
                    self.stdout.write(f"{inicio.strftime('%H:%M:%S')} - No hay operaciones pendientes")
                
                # Esperar hasta el próximo ciclo
                time.sleep(intervalo)
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS("\nModo continuo finalizado por el usuario"))
            return
