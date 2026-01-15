
import os
import django
from django.conf import settings
from django.db.models import Count, Sum

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from orders.models import Order

print("Order Status Counts:")
print(Order.objects.values('status').annotate(count=Count('id'), total_val=Sum('total')))

print("\nRecent Orders:")
for o in Order.objects.order_by('-created_at')[:5]:
    print(f"ID: {o.id}, Status: {o.status}, Total: {o.total}, Created: {o.created_at}")
