import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from orders.models import Order
try:
    order = Order.objects.get(id=2)
    print(f"Order 2 exists: {order}")
except Order.DoesNotExist:
    print("Order 2 DOES NOT exist")
except Exception as e:
    print(f"Error: {e}")
