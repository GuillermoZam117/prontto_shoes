import datetime
from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal

from clientes.models import Cliente, DescuentoCliente
from ventas.models import Pedido
from descuentos.models import TabuladorDescuento

class Command(BaseCommand):
    help = "Manually recalculate discounts for clients for a specific target month based on a specific source month's sales."

    def add_arguments(self, parser):
        # Source month for sales data (format: YYYY-MM)
        parser.add_argument('--source-month', type=str, help='Month to use for sales data in YYYY-MM format')
        
        # Target month for discount application (format: YYYY-MM)
        parser.add_argument('--target-month', type=str, help='Month to calculate discounts for in YYYY-MM format')
        
        # Optional client ID to recalculate for a specific client only
        parser.add_argument('--client-id', type=int, help='Optional: Recalculate only for a specific client ID')

    def handle(self, *args, **options):
        # Parse source month, default to previous month
        source_month = options.get('source_month')
        if source_month:
            try:
                source_year, source_month_num = map(int, source_month.split('-'))
                first_day_of_source_month = datetime.date(source_year, source_month_num, 1)
                last_day_of_source_month = (
                    datetime.date(source_year + (source_month_num//12), 
                                 ((source_month_num % 12) + 1) if source_month_num < 12 else 1, 
                                 1) - datetime.timedelta(days=1)
                )
            except ValueError:
                self.stdout.write(self.style.ERROR('Invalid source month format. Use YYYY-MM.'))
                return
        else:
            # Default to previous month
            today = timezone.now().date()
            first_day_of_current_month = today.replace(day=1)
            last_day_of_previous_month = first_day_of_current_month - datetime.timedelta(days=1)
            first_day_of_source_month = last_day_of_previous_month.replace(day=1)
            last_day_of_source_month = last_day_of_previous_month
            source_month = first_day_of_source_month.strftime('%Y-%m')

        # Parse target month, default to current month
        target_month = options.get('target_month')
        if not target_month:
            # Default to current month
            target_month = timezone.now().date().strftime('%Y-%m')
            
        self.stdout.write(f'Recalculating discounts for {target_month} based on sales from {source_month}...')

        # Apply client filter if specified
        client_filter = {}
        client_id = options.get('client_id')
        if client_id:
            client_filter['id'] = client_id
            self.stdout.write(f'Filtering for client ID: {client_id}')

        # Calculate total sales for each client in the specified source month
        client_sales_query = Pedido.objects.filter(
            fecha__date__gte=first_day_of_source_month,
            fecha__date__lte=last_day_of_source_month,
            tipo='venta',  # Only consider sales, not preventative orders
            estado='surtido',  # Only consider completed orders
            pagado=True  # Only consider paid orders for discounts
        )
        
        if client_id:
            client_sales_query = client_sales_query.filter(cliente_id=client_id)
            
        client_sales = client_sales_query.values('cliente').annotate(total_ventas=Sum('total'))

        # Get all discount tiers sorted by range
        tabulador = list(TabuladorDescuento.objects.all().order_by('rango_min'))

        # Log if no tiers are found
        if not tabulador:
            self.stdout.write(self.style.WARNING('No discount tiers found in the system. Using 0% as default.'))
        
        # Process each client's sales data
        total_processed = 0
        total_updated = 0
        total_created = 0
        
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

                # Create or update DescuentoCliente entry for the target month
                descuento_cliente, created = DescuentoCliente.objects.update_or_create(
                    cliente=cliente,
                    mes_vigente=target_month,
                    defaults={
                        'porcentaje': assigned_discount_percentage,
                        'monto_acumulado_mes_anterior': total_ventas
                    }
                )

                status = 'Created' if created else 'Updated'
                if created:
                    total_created += 1
                else:
                    total_updated += 1
                    
                total_processed += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{status} {assigned_discount_percentage}% discount for {cliente.nombre} for {target_month} based on {total_ventas} in sales.'
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

        self.stdout.write(self.style.SUCCESS(
            f'Discount recalculation complete. Processed: {total_processed}, '
            f'Created: {total_created}, Updated: {total_updated}')
        )
