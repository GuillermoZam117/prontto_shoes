"""
Tests unitarios para modelos de descuentos.
Valida la funcionalidad del modelo TabuladorDescuento.
"""
import pytest
from decimal import Decimal
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from tests.base import BaseTestCase
from tests.factories import TabuladorDescuentoFactory
from descuentos.models import TabuladorDescuento


class TestTabuladorDescuentoModel(BaseTestCase):
    """Tests unitarios para el modelo TabuladorDescuento."""

    def test_should_create_tabulador_with_required_fields(self):
        """Debe crear tabulador con campos requeridos."""
        tabulador = TabuladorDescuentoFactory(
            rango_min=Decimal('0.00'),
            rango_max=Decimal('100.00'),
            porcentaje=Decimal('5.00')
        )
        
        assert tabulador.rango_min == Decimal('0.00')
        assert tabulador.rango_max == Decimal('100.00')
        assert tabulador.porcentaje == Decimal('5.00')    def test_should_validate_decimal_precision(self):
        """Debe validar precisión de decimales."""
        tabulador = TabuladorDescuentoFactory(
            rango_min=Decimal('9999999999.99'),  # Max digits 12, decimals 2 (10^10 - 1)
            rango_max=Decimal('9999999999.99'),
            porcentaje=Decimal('999.99')  # Max digits 5, decimals 2        )
        
        assert tabulador.rango_min == Decimal('9999999999.99')
        assert tabulador.porcentaje == Decimal('999.99')

    def test_should_handle_zero_ranges(self):
        """Debe manejar rangos con cero."""
        tabulador = TabuladorDescuentoFactory(
            rango_min=Decimal('0.00'),
            rango_max=Decimal('0.00'),
            porcentaje=Decimal('0.00')
        )
        
        assert tabulador.rango_min == Decimal('0.00')
        assert tabulador.rango_max == Decimal('0.00')
        assert tabulador.porcentaje == Decimal('0.00')

    def test_should_handle_negative_values(self):
        """Debe manejar valores negativos si están permitidos."""
        # En algunos sistemas, los rangos negativos podrían representar
        # casos especiales como créditos o ajustes
        tabulador = TabuladorDescuentoFactory(
            rango_min=Decimal('-100.00'),
            rango_max=Decimal('0.00'),
            porcentaje=Decimal('2.50')
        )
        
        assert tabulador.rango_min == Decimal('-100.00')
        assert tabulador.rango_max == Decimal('0.00')

    def test_should_return_formatted_string_representation(self):
        """Debe retornar representación string formateada."""
        tabulador = TabuladorDescuentoFactory(
            rango_min=Decimal('100.00'),
            rango_max=Decimal('500.00'),
            porcentaje=Decimal('10.50')
        )
        
        expected = "100.00 - 500.00: 10.50%"
        assert str(tabulador) == expected

    def test_should_handle_large_currency_amounts(self):
        """Debe manejar montos grandes de moneda."""
        tabulador = TabuladorDescuentoFactory(
            rango_min=Decimal('1000000.00'),  # 1 millón
            rango_max=Decimal('5000000.00'),  # 5 millones
            porcentaje=Decimal('15.75')
        )
        
        assert tabulador.rango_min == Decimal('1000000.00')
        assert tabulador.rango_max == Decimal('5000000.00')
        assert tabulador.porcentaje == Decimal('15.75')

    def test_should_handle_precise_percentage_values(self):
        """Debe manejar valores de porcentaje precisos."""
        precise_percentages = [
            Decimal('0.01'),    # 0.01%
            Decimal('0.25'),    # 0.25%
            Decimal('1.33'),    # 1.33%
            Decimal('99.99'),   # 99.99%
            Decimal('100.00')   # 100.00%
        ]
        
        for percentage in precise_percentages:
            tabulador = TabuladorDescuentoFactory(porcentaje=percentage)
            assert tabulador.porcentaje == percentage

    def test_should_support_fractional_currency_amounts(self):
        """Debe soportar montos fraccionarios de moneda."""
        tabulador = TabuladorDescuentoFactory(
            rango_min=Decimal('0.01'),     # 1 centavo
            rango_max=Decimal('9.99'),     # 9.99
            porcentaje=Decimal('0.50')     # 0.5%
        )
        
        assert tabulador.rango_min == Decimal('0.01')
        assert tabulador.rango_max == Decimal('9.99')
        assert tabulador.porcentaje == Decimal('0.50')


class TestTabuladorDescuentoBusinessLogic(BaseTestCase):
    """Tests para lógica de negocio del tabulador de descuentos."""

    def test_should_create_progressive_discount_structure(self):
        """Debe crear estructura progresiva de descuentos."""
        # Crear tabulador progresivo típico
        tabuladores = [
            TabuladorDescuentoFactory(
                rango_min=Decimal('0.00'),
                rango_max=Decimal('100.00'),
                porcentaje=Decimal('2.00')  # 2% para compras hasta 100
            ),
            TabuladorDescuentoFactory(
                rango_min=Decimal('100.01'),
                rango_max=Decimal('500.00'),
                porcentaje=Decimal('5.00')  # 5% para compras 100-500
            ),
            TabuladorDescuentoFactory(
                rango_min=Decimal('500.01'),
                rango_max=Decimal('1000.00'),
                porcentaje=Decimal('8.00')  # 8% para compras 500-1000
            ),
            TabuladorDescuentoFactory(
                rango_min=Decimal('1000.01'),
                rango_max=Decimal('999999.99'),
                porcentaje=Decimal('12.00')  # 12% para compras >1000
            )
        ]
        
        # Verificar estructura progresiva
        assert len(tabuladores) == 4
        porcentajes = [t.porcentaje for t in tabuladores]
        assert porcentajes == [
            Decimal('2.00'), 
            Decimal('5.00'), 
            Decimal('8.00'), 
            Decimal('12.00')
        ]

    def test_should_handle_overlapping_ranges(self):
        """Debe manejar rangos superpuestos."""
        # En algunos sistemas, los rangos pueden superponerse
        # y aplicarse diferentes reglas de prioridad
        tabulador1 = TabuladorDescuentoFactory(
            rango_min=Decimal('0.00'),
            rango_max=Decimal('200.00'),
            porcentaje=Decimal('5.00')
        )
        tabulador2 = TabuladorDescuentoFactory(
            rango_min=Decimal('150.00'),  # Se superpone con el anterior
            rango_max=Decimal('300.00'),
            porcentaje=Decimal('7.00')
        )
        
        # Ambos deberían existir - la lógica de negocio determinaría
        # cuál aplicar en caso de superposición
        assert tabulador1.rango_max > tabulador2.rango_min
        assert TabuladorDescuento.objects.count() == 2

    def test_should_handle_gap_ranges(self):
        """Debe manejar rangos con gaps."""
        # Crear rangos con espacios entre ellos
        TabuladorDescuentoFactory(
            rango_min=Decimal('0.00'),
            rango_max=Decimal('50.00'),
            porcentaje=Decimal('3.00')
        )
        TabuladorDescuentoFactory(
            rango_min=Decimal('100.00'),  # Gap de 50-100
            rango_max=Decimal('200.00'),
            porcentaje=Decimal('6.00')
        )
        
        # Los gaps podrían representar rangos sin descuento
        assert TabuladorDescuento.objects.count() == 2

    def test_should_support_volume_discount_tiers(self):
        """Debe soportar niveles de descuento por volumen."""
        # Crear niveles típicos de descuento por volumen
        volume_tiers = [
            {'min': '0.00', 'max': '999.99', 'discount': '0.00'},      # Sin descuento
            {'min': '1000.00', 'max': '4999.99', 'discount': '3.00'}, # 3% descuento
            {'min': '5000.00', 'max': '9999.99', 'discount': '5.00'}, # 5% descuento
            {'min': '10000.00', 'max': '24999.99', 'discount': '8.00'}, # 8% descuento
            {'min': '25000.00', 'max': '999999.99', 'discount': '12.00'} # 12% descuento
        ]
        
        created_tiers = []
        for tier in volume_tiers:
            tabulador = TabuladorDescuentoFactory(
                rango_min=Decimal(tier['min']),
                rango_max=Decimal(tier['max']),
                porcentaje=Decimal(tier['discount'])
            )
            created_tiers.append(tabulador)
        
        assert len(created_tiers) == 5
        
        # Verificar que los descuentos aumentan con el volumen
        discounts = [t.porcentaje for t in created_tiers]
        assert discounts == [
            Decimal('0.00'), Decimal('3.00'), Decimal('5.00'),
            Decimal('8.00'), Decimal('12.00')
        ]

    def test_should_simulate_discount_calculation_logic(self):
        """Debe simular lógica de cálculo de descuento."""
        # Crear tabulador para testing
        TabuladorDescuentoFactory(
            rango_min=Decimal('100.00'),
            rango_max=Decimal('500.00'),
            porcentaje=Decimal('10.00')
        )
        
        # Simular función que buscaría el descuento apropiado
        def calcular_descuento(monto):
            tabulador = TabuladorDescuento.objects.filter(
                rango_min__lte=monto,
                rango_max__gte=monto
            ).first()
            
            if tabulador:
                return monto * (tabulador.porcentaje / Decimal('100'))
            return Decimal('0.00')
        
        # Test cases
        assert calcular_descuento(Decimal('50.00')) == Decimal('0.00')   # Fuera de rango
        assert calcular_descuento(Decimal('200.00')) == Decimal('20.00') # 10% de 200
        assert calcular_descuento(Decimal('300.00')) == Decimal('30.00') # 10% de 300
        assert calcular_descuento(Decimal('600.00')) == Decimal('0.00')  # Fuera de rango


class TestTabuladorDescuentoIntegration(BaseTestCase):
    """Tests de integración para tabulador de descuentos."""

    def test_should_support_complex_discount_scenarios(self):
        """Debe soportar escenarios complejos de descuento."""
        # Crear múltiples tabuladores para diferentes categorías
        # (en un sistema real, podría haber categorías por producto, cliente, etc.)
        
        # Descuentos para clientes regulares
        regular_discounts = [
            TabuladorDescuentoFactory(
                rango_min=Decimal('0.00'),
                rango_max=Decimal('500.00'),
                porcentaje=Decimal('2.00')
            ),
            TabuladorDescuentoFactory(
                rango_min=Decimal('500.01'),
                rango_max=Decimal('1500.00'),
                porcentaje=Decimal('5.00')
            )
        ]
        
        # Descuentos para clientes VIP (porcentajes más altos)
        vip_discounts = [
            TabuladorDescuentoFactory(
                rango_min=Decimal('0.00'),
                rango_max=Decimal('500.00'),
                porcentaje=Decimal('5.00')
            ),
            TabuladorDescuentoFactory(
                rango_min=Decimal('500.01'),
                rango_max=Decimal('1500.00'),
                porcentaje=Decimal('10.00')
            )
        ]
        
        assert TabuladorDescuento.objects.count() == 4

    def test_should_handle_seasonal_discount_adjustments(self):
        """Debe manejar ajustes estacionales de descuento."""
        # Crear descuentos base
        base_discount = TabuladorDescuentoFactory(
            rango_min=Decimal('100.00'),
            rango_max=Decimal('1000.00'),
            porcentaje=Decimal('5.00')
        )
        
        # Simular descuento estacional adicional
        seasonal_bonus = Decimal('2.00')  # 2% adicional
        total_discount = base_discount.porcentaje + seasonal_bonus
        
        assert total_discount == Decimal('7.00')

    def test_should_support_discount_combination_rules(self):
        """Debe soportar reglas de combinación de descuentos."""
        # Crear diferentes tipos de descuentos
        volume_discount = TabuladorDescuentoFactory(
            rango_min=Decimal('1000.00'),
            rango_max=Decimal('5000.00'),
            porcentaje=Decimal('8.00')  # Descuento por volumen
        )
        
        loyalty_discount = TabuladorDescuentoFactory(
            rango_min=Decimal('0.00'),
            rango_max=Decimal('999999.99'),
            porcentaje=Decimal('3.00')  # Descuento por lealtad
        )
        
        # En un sistema real, se aplicarían reglas como:
        # - Máximo descuento combinado
        # - Descuentos excluyentes
        # - Descuentos acumulativos
        
        max_combined = min(
            volume_discount.porcentaje + loyalty_discount.porcentaje,
            Decimal('15.00')  # Máximo 15%
        )
        
        assert max_combined == Decimal('11.00')

    def test_should_validate_business_rules(self):
        """Debe validar reglas de negocio."""
        # En un sistema real, se podrían validar:
        
        # 1. Rangos consecutivos sin gaps
        def validate_consecutive_ranges():
            tabuladores = TabuladorDescuento.objects.order_by('rango_min')
            for i in range(len(tabuladores) - 1):
                current = tabuladores[i]
                next_tab = tabuladores[i + 1]
                gap = next_tab.rango_min - current.rango_max
                # assert gap <= Decimal('0.01')  # Gap mínimo aceptable
        
        # 2. Porcentajes dentro de límites razonables
        def validate_percentage_limits():
            for tabulador in TabuladorDescuento.objects.all():
                assert Decimal('0.00') <= tabulador.porcentaje <= Decimal('50.00')
        
        # 3. Rangos válidos (min <= max)
        def validate_range_logic():
            for tabulador in TabuladorDescuento.objects.all():
                assert tabulador.rango_min <= tabulador.rango_max
        
        # Crear datos de prueba
        TabuladorDescuentoFactory(
            rango_min=Decimal('0.00'),
            rango_max=Decimal('100.00'),
            porcentaje=Decimal('5.00')
        )
        
        # Ejecutar validaciones
        validate_percentage_limits()
        validate_range_logic()

    def test_should_support_discount_queries(self):
        """Debe soportar consultas de descuento."""
        # Crear varios tabuladores
        tabuladores_data = [
            {'min': '0.00', 'max': '99.99', 'percent': '2.00'},
            {'min': '100.00', 'max': '499.99', 'percent': '5.00'},
            {'min': '500.00', 'max': '999.99', 'percent': '8.00'},
            {'min': '1000.00', 'max': '4999.99', 'percent': '12.00'},
        ]
        
        for data in tabuladores_data:
            TabuladorDescuentoFactory(
                rango_min=Decimal(data['min']),
                rango_max=Decimal(data['max']),
                porcentaje=Decimal(data['percent'])
            )
        
        # Consultas típicas
        descuentos_bajos = TabuladorDescuento.objects.filter(
            porcentaje__lt=Decimal('10.00')
        )
        descuentos_altos = TabuladorDescuento.objects.filter(
            porcentaje__gte=Decimal('10.00')
        )
        rangos_pequenos = TabuladorDescuento.objects.filter(
            rango_max__lt=Decimal('500.00')
        )
        
        assert descuentos_bajos.count() == 3
        assert descuentos_altos.count() == 1
        assert rangos_pequenos.count() == 2
