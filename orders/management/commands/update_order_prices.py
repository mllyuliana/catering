from django.core.management.base import BaseCommand
from orders.models import Order

class Command(BaseCommand):
    help = 'Updates total_price for all orders'

    def handle(self, *args, **options):
        orders = Order.objects.all()
        updated_count = 0
        
        for order in orders:
            order.save()  # This will trigger the save method that updates total_price
            updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} orders')
        ) 