import os
import django
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
import json
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from orders.models import Order, OrderItem
from products.models import Product
from users.models import User

def debug_api():
    print("--- Debugging NEW admin_stats_api logic ---")
    
    # Time window (Last 30 days)
    now = timezone.now()
    last_30_days = now - timedelta(days=30)
    
    # 2. Sales Chart (Daily Revenue last 30 days) - PROPER TIMELINE
    raw_sales_data = Order.objects.filter(created_at__gte=last_30_days).exclude(status__in=['cancelled', 'returned']) \
        .annotate(date=TruncDate('created_at')) \
        .values('date') \
        .annotate(daily_revenue=Sum('total')) \
        .order_by('date')
    
    sales_map = {s['date'].strftime('%Y-%m-%d'): float(s['daily_revenue']) for s in raw_sales_data}
    
    labels = []
    revenue_points = []
    for i in range(30, -1, -1):
        day = (now - timedelta(days=i)).strftime('%Y-%m-%d')
        labels.append(day)
        revenue_points.append(sales_map.get(day, 0.0))

    print(f"Number of data points: {len(revenue_points)}")
    print("Labels (first 5):", labels[:5])
    print("Revenue (first 5):", revenue_points[:5])
    print("Labels (last 5):", labels[-5:])
    print("Revenue (last 5):", revenue_points[-5:])

    # Check for gaps
    if len(revenue_points) == 31:
        print("SUCCESS: Timeline is continuous with 31 points (30 days + today).")
    else:
        print(f"FAILURE: Expected 31 points, got {len(revenue_points)}.")

if __name__ == "__main__":
    debug_api()
