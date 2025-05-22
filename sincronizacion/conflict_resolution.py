"""
Sistema de resolución de conflictos para el módulo de sincronización.

Este módulo proporciona mecanismos para detectar y resolver conflictos
que puedan surgir durante la sincronización de datos entre tiendas.
"""
import logging
import json
from enum import Enum
from django.db.models import Q
from django.utils import timezone
from .models import ColaSincronizacion, EstadoSincronizacion, TipoOperacion
from .websocket import notificar_conflicto

logger = logging.getLogger(__name__)

class ConflictResolutionStrategy(Enum):
    """Estrategias disponibles para resolución de conflictos"""
    ULTIMA_MODIFICACION = 'ultima_modificacion'  # Prioriza el cambio más reciente
    PRIORIDAD_CENTRAL = 'prioridad_central'      # Prioriza cambios desde tienda central
    MEZCLAR_CAMPOS = 'mezclar_campos'            # Mezcla campos según reglas específicas
    MANUAL = 'manual'                            # Requiere intervención manual


class ConflictResolver:
    """
    Gestor de resolución de conflictos para sincronización.
    
    Proporciona funcionalidades para:
    - Detectar conflictos entre operaciones
    - Resolver conflictos automáticamente según diferentes estrategias
    - Mezclar datos de diferentes fuentes
    - Mantener historial de resoluciones
    """
    
    def detectar_conflictos(self, modelo_tipo=None, modelo_id=None, codigo=None):
        """
        Detecta conflictos entre operaciones pendientes sobre el mismo objeto.
        
        Args:
            modelo_tipo (str, optional): Tipo de modelo (app_label.model_name).
            modelo_id (int, optional): ID del objeto.
            codigo (str, optional): Código del objeto (alternativa a ID).
            
        Returns:
            list: Lista de operaciones en conflicto.
        """
        # Base query - operaciones en estado CONFLICTO o PENDIENTE
        query = ColaSincronizacion.objects.filter(
            estado__in=[EstadoSincronizacion.CONFLICTO, EstadoSincronizacion.PENDIENTE]
        )
        
        # Filtrar por modelo
        if modelo_tipo:
            query = query.filter(modelo_tipo=modelo_tipo)
        
        # Filtrar por ID o código
        if modelo_id:
            query = query.filter(modelo_id=modelo_id)
        elif codigo:
            # Buscar en datos.codigo si existe
            query = query.filter(
                Q(datos__contains=f'"codigo":"{codigo}"') | 
                Q(datos__contains=f'"codigo": "{codigo}"')
            )
        
        # Encontrar grupos de conflictos
        conflicts = []
        processed_ids = set()
        
        for operation in query:
            if operation.id in processed_ids:
                continue
                
            # Encuentra operaciones que afecten al mismo objeto
            related_operations = None
            
            if codigo and not modelo_id:
                # Si tenemos código pero no ID, usamos el código para buscar conflictos
                related_operations = query.filter(
                    Q(datos__contains=f'"codigo":"{codigo}"') | 
                    Q(datos__contains=f'"codigo": "{codigo}"')
                ).exclude(id=operation.id)
            else:
                # Si tenemos ID, usamos el ID para buscar conflictos
                related_operations = query.filter(
                    modelo_tipo=operation.modelo_tipo,
                    modelo_id=operation.modelo_id
                ).exclude(id=operation.id)
            
            # Si hay operaciones relacionadas, tenemos un conflicto
            if related_operations.exists():
                conflicts.append(operation)
                for related in related_operations:
                    conflicts.append(related)
                    processed_ids.add(related.id)
                
                # Marcar operaciones como en conflicto si no lo están ya
                for conflict_op in [operation] + list(related_operations):
                    if conflict_op.estado != EstadoSincronizacion.CONFLICTO:
                        conflict_op.estado = EstadoSincronizacion.CONFLICTO
                        conflict_op.save(update_fields=['estado', 'fecha_modificacion'])
                        
                        # Notificar conflicto
                        mensaje = f"Conflicto detectado para {conflict_op.modelo_tipo} (ID: {conflict_op.modelo_id})"
                        notificar_conflicto(conflict_op, mensaje)
            
            processed_ids.add(operation.id)
            
        return conflicts
    
    def resolver_conflicto(self, operacion1, operacion2, strategy=ConflictResolutionStrategy.ULTIMA_MODIFICACION, field_priorities=None):
        """
        Resuelve un conflicto entre dos operaciones.
        
        Args:
            operacion1 (ColaSincronizacion): Primera operación.
            operacion2 (ColaSincronizacion): Segunda operación.
            strategy (ConflictResolutionStrategy): Estrategia a aplicar.
            field_priorities (dict, optional): Prioridades por campo para MEZCLAR_CAMPOS.
                Ejemplo: {'nombre': 'central', 'precio': 'ultima_modificacion', 'stock': 'sumar'}
            
        Returns:
            ColaSincronizacion: Operación resultante (ganadora o fusionada).
        """
        if strategy == ConflictResolutionStrategy.ULTIMA_MODIFICACION:
            # La operación más reciente gana
            if operacion1.fecha_modificacion > operacion2.fecha_modificacion:
                return self._marcar_ganador(operacion1, operacion2)
            else:
                return self._marcar_ganador(operacion2, operacion1)
                
        elif strategy == ConflictResolutionStrategy.PRIORIDAD_CENTRAL:
            # La operación de la tienda central gana
            if operacion1.tienda_origen.es_central:
                return self._marcar_ganador(operacion1, operacion2)
            elif operacion2.tienda_origen.es_central:
                return self._marcar_ganador(operacion2, operacion1)
            else:
                # Si ninguna es de la tienda central, usar última modificación
                return self.resolver_conflicto(operacion1, operacion2, ConflictResolutionStrategy.ULTIMA_MODIFICACION)
                
        elif strategy == ConflictResolutionStrategy.MEZCLAR_CAMPOS:
            # Mezclar campos según las prioridades especificadas
            if not field_priorities:
                field_priorities = {}
                
            # Crear una nueva operación mezclada
            return self._mezclar_operaciones(operacion1, operacion2, field_priorities)
                
        elif strategy == ConflictResolutionStrategy.MANUAL:
            # Mantener en estado de conflicto para resolución manual
            operacion1.estado = EstadoSincronizacion.CONFLICTO
            operacion2.estado = EstadoSincronizacion.CONFLICTO
            operacion1.save(update_fields=['estado', 'fecha_modificacion'])
            operacion2.save(update_fields=['estado', 'fecha_modificacion'])
            return None
            
        # Por defecto, usar última modificación
        return self.resolver_conflicto(operacion1, operacion2, ConflictResolutionStrategy.ULTIMA_MODIFICACION)
    
    def resolver_todos_conflictos(self, modelo_tipo=None, modelo_id=None, codigo=None, strategy=ConflictResolutionStrategy.ULTIMA_MODIFICACION, field_priorities=None):
        """
        Resuelve todos los conflictos para un tipo de modelo/objeto específico.
        
        Args:
            modelo_tipo (str, optional): Tipo de modelo (app_label.model_name).
            modelo_id (int, optional): ID del objeto.
            codigo (str, optional): Código del objeto (alternativa a ID).
            strategy (ConflictResolutionStrategy): Estrategia a aplicar.
            field_priorities (dict, optional): Prioridades por campo para MEZCLAR_CAMPOS.
            
        Returns:
            list: Lista de operaciones resultantes tras la resolución.
        """
        conflicts = self.detectar_conflictos(modelo_tipo, modelo_id, codigo)
        
        if not conflicts:
            return []
            
        # Agrupar conflictos por modelo/objeto
        conflict_groups = {}
        for operation in conflicts:
            key = f"{operation.modelo_tipo}_{operation.modelo_id}"
            if key not in conflict_groups:
                conflict_groups[key] = []
            conflict_groups[key].append(operation)
            
        # Resolver cada grupo de conflictos
        results = []
        for group in conflict_groups.values():
            if len(group) < 2:
                continue
                
            # Iniciar con la primera operación como ganadora temporal
            winner = group[0]
            
            # Comparar con cada operación restante
            for i in range(1, len(group)):
                winner = self.resolver_conflicto(winner, group[i], strategy, field_priorities)
                
            if winner:
                results.append(winner)
                
        return results
    
    def _marcar_ganador(self, winner, loser):
        """
        Marca una operación como ganadora y la otra como completada.
        
        Args:
            winner (ColaSincronizacion): Operación ganadora.
            loser (ColaSincronizacion): Operación perdedora.
            
        Returns:
            ColaSincronizacion: Operación ganadora actualizada.
        """
        # Actualizar operación ganadora
        winner.estado = EstadoSincronizacion.PENDIENTE
        winner.fecha_modificacion = timezone.now()
        winner.save(update_fields=['estado', 'fecha_modificacion'])
        
        # Marcar perdedora como completada
        loser.estado = EstadoSincronizacion.COMPLETADO
        loser.fecha_modificacion = timezone.now()
        loser.save(update_fields=['estado', 'fecha_modificacion'])
        
        logger.info(f"Conflicto resuelto: Operación {winner.id} ganó sobre {loser.id}")
        
        return winner
    
    def _mezclar_operaciones(self, op1, op2, field_priorities):
        """
        Mezcla dos operaciones según prioridades de campo.
        
        Args:
            op1 (ColaSincronizacion): Primera operación.
            op2 (ColaSincronizacion): Segunda operación.
            field_priorities (dict): Prioridades por campo.
                Posibles valores: 'central', 'ultima_modificacion', 'sumar', 'local'
            
        Returns:
            ColaSincronizacion: Operación mezclada (se usa op1 como base).
        """
        # Obtener datos como dicts
        datos1 = op1.datos if isinstance(op1.datos, dict) else json.loads(op1.datos)
        datos2 = op2.datos if isinstance(op2.datos, dict) else json.loads(op2.datos)
        
        # Identificar operación de tienda central (si alguna lo es)
        op_central = op1 if op1.tienda_origen.es_central else (op2 if op2.tienda_origen.es_central else None)
        op_local = op2 if op_central == op1 else op1
        
        # Crear datos mezclados
        merged_data = datos1.copy()
        
        # Recorrer todos los campos
        all_fields = set(list(datos1.keys()) + list(datos2.keys()))
        
        for field in all_fields:
            # Valores de cada operación (si existen)
            val1 = datos1.get(field)
            val2 = datos2.get(field)
            
            # Si solo existe en una operación, usar ese valor
            if field not in datos1:
                merged_data[field] = val2
                continue
            elif field not in datos2:
                merged_data[field] = val1
                continue
                
            # Aplicar estrategia según prioridad del campo
            field_strategy = field_priorities.get(field, 'ultima_modificacion')
            
            if field_strategy == 'central' and op_central:
                # Usar valor de tienda central
                merged_data[field] = datos1[field] if op_central == op1 else datos2[field]
                
            elif field_strategy == 'local' and op_local:
                # Usar valor de tienda local
                merged_data[field] = datos1[field] if op_local == op1 else datos2[field]
                
            elif field_strategy == 'ultima_modificacion':
                # Usar valor de la operación más reciente
                if op1.fecha_modificacion > op2.fecha_modificacion:
                    merged_data[field] = val1
                else:
                    merged_data[field] = val2
                    
            elif field_strategy == 'sumar' and isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                # Sumar valores numéricos
                merged_data[field] = val1 + val2
                
            # En cualquier otro caso, mantener el valor de op1 (base)
        
        # Usar op1 como base para la operación resultante
        op1.datos = merged_data
        op1.estado = EstadoSincronizacion.PENDIENTE
        op1.fecha_modificacion = timezone.now()
        op1.save()
        
        # Marcar op2 como completada
        op2.estado = EstadoSincronizacion.COMPLETADO
        op2.fecha_modificacion = timezone.now()
        op2.save(update_fields=['estado', 'fecha_modificacion'])
        
        logger.info(f"Operaciones mezcladas: {op1.id} y {op2.id}")
        
        return op1


# Instancia global del resolutor de conflictos
conflict_resolver = ConflictResolver()
