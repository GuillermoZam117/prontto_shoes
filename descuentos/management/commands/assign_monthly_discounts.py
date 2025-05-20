import datetime
from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal

from clientes.models import Cliente, DescuentoCliente
from ventas.models import Pedido
from descuentos.models import TabuladorDescuento

class Command(BaseCommand):
    help = "Assigns monthly discounts to clients based on previous month's sales."

    def handle(self, *args, **options):
        self.stdout.write('Calculating and assigning monthly discounts...')

        today = timezone.now().date()
        first_day_of_current_month = today.replace(day=1)
        last_day_of_previous_month = first_day_of_current_month - datetime.timedelta(days=1)
        first_day_of_previous_month = last_day_of_previous_month.replace(day=1)

        current_month_str = today.strftime('%Y-%m')

        # Calculate total sales for each client in the previous month
        client_sales = Pedido.objects.filter(
            fecha__date__gte=first_day_of_previous_month,
            fecha__date__lte=last_day_of_previous_month,
            tipo='venta', # Only consider sales, not preventative orders
            estado='surtido'  # Only consider completed orders
        ).values('cliente').annotate(total_ventas=Sum('total'))

        tabulador = list(TabuladorDescuento.objects.all().order_by('rango_min'))

        # Log if no tiers are found
        if not tabulador:
            self.stdout.write(self.style.WARNING('No discount tiers found in the system. Using 0% as default.'))
        
        for sales_data in client_sales:
            cliente_id = sales_data['cliente']
            total_ventas = sales_data['total_ventas'] or Decimal('0')

            try:
                cliente = Cliente.objects.get(id=cliente_id)
                assigned_discount_percentage = Decimal('0')

                # Find the appropriate discount tier
                for tier in tabulador:
                    if tier.rango_min <= total_ventas <= tier.rango_max:
                        assigned_discount_percentage = tier.porcentaje
                        break

                # Create or update DescuentoCliente entry for the current month
                descuento_cliente, created = DescuentoCliente.objects.update_or_create(
                    cliente=cliente,
                    mes_vigente=current_month_str,
                    defaults={
                        'porcentaje': assigned_discount_percentage,
                        'monto_acumulado_mes_anterior': total_ventas
                    }
                )

                status = 'Created' if created else 'Updated'
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{status} {assigned_discount_percentage}% discount for {cliente.nombre} for {current_month_str} based on {total_ventas} in sales.'
                    )
                )
            except Cliente.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Client with ID {cliente_id} not found. Skipping.')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing client with ID {cliente_id}: {str(e)}')
                )

        self.stdout.write(self.style.SUCCESS('Monthly discount assignment complete.'))
 