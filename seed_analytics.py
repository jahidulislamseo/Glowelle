import os
import django
import sys

sys.path.append(os.path.abspath('c:/Users/Jahidul-islam/Desktop/all apk and website/al-barakah-mart-django'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from orders.models import Order
from django.utils import timezone
from datetime import timedelta
import random

orders = Order.objects.all()
if not orders.exists():
    print("No orders to update!")
else:
    print(f"Updating {orders.count()} orders...")
    for i, order in enumerate(orders):
        # Mark some as delivered, some processing
        if i % 2 == 0:
            order.status = 'delivered'
            # Spread dates over last 30 days
            order.created_at = timezone.now() - timedelta(days=random.randint(1, 28))
        else:
            order.status = 'processing'
            order.created_at = timezone.now() - timedelta(days=random.randint(0, 5))
            
        order.save()
        print(f"Updated Order #{order.id} to {order.status}")

print("Done updates.")
