"""
Test script to verify chatbot order creation and user linking.
Run this to check if orders are being created correctly.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')
django.setup()

from orders.models import Order
from users.models import User

def test_chatbot_orders():
    print("\n=== Testing Chatbot Order Creation ===\n")
    
    # Check all orders
    all_orders = Order.objects.all().order_by('-created_at')
    print(f"Total Orders in Database: {all_orders.count()}")
    
    # Check orders with user
    orders_with_user = Order.objects.exclude(user=None).count()
    print(f"Orders with User Link: {orders_with_user}")
    
    # Check orders without user
    orders_without_user = Order.objects.filter(user=None).count()
    print(f"Orders WITHOUT User Link: {orders_without_user}")
    
    # Show recent orders
    print("\n=== Recent Orders (Last 5) ===")
    for order in all_orders[:5]:
        print(f"\nOrder #{order.order_reference}")
        print(f"  User: {order.user if order.user else 'NO USER LINKED'}")
        print(f"  Phone: {order.phone}")
        print(f"  Email: {order.email}")
        print(f"  Name: {order.full_name}")
        print(f"  Total: {order.total} BDT")
        print(f"  Status: {order.status}")
        print(f"  Source: {order.source}")
    
    # Check users and their orders
    print("\n=== Users with Orders ===")
    users_with_orders = User.objects.filter(orders__isnull=False).distinct()
    for user in users_with_orders[:5]:
        order_count = user.orders.count()
        print(f"\nUser: {user.username} ({user.phone})")
        print(f"  Total Orders: {order_count}")
        print(f"  Email: {user.email}")

if __name__ == "__main__":
    test_chatbot_orders()
