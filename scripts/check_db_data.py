import os
import django
import sys

# Add project root to path
sys.path.append(os.path.abspath('c:/Users/Jahidul-islam/Desktop/all apk and website/al-barakah-mart-django'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from orders.models import Order
from users.models import User

print(f"Total Users: {User.objects.count()}")
print(f"Total Orders: {Order.objects.count()}")
print(f"Delivered Orders: {Order.objects.filter(status='delivered').count()}")
print(f"Recent Orders (30d): {Order.objects.all().count()}")
