import os
import django
from django.conf import settings
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection, reset_queries

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Fix ALLOWED_HOSTS for RequestFactory
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ['testserver']

from products.views import home, wishlist_view, shop
from orders.views import order_detail
from orders.models import Order
from products.models import Product

def verify_optimizations():
    factory = RequestFactory()
    User = get_user_model()
    
    # Create or get a test user
    user, created = User.objects.get_or_create(username='testoptimizer', email='opt@test.com')
    if created:
        user.set_password('password123')
        user.save()

    print("--- Verifying Home View Caching ---")
    request = factory.get('/')
    request.user = user
    request.session = {} 
    
    # Warm up cache
    cache.clear()
    reset_queries()
    response = home(request)
    initial_query_count = len(connection.queries)
    print(f"Home View (First Hit): {response.status_code}, Queries: {initial_query_count}")

    # Cached Hit
    reset_queries()
    response = home(request)
    cached_query_count = len(connection.queries)
    print(f"Home View (Cached Hit): {response.status_code}, Queries: {cached_query_count}")
    
    if cached_query_count < initial_query_count:
        print("SUCCESS: Caching is working! (Queries reduced)")
    else:
        print("WARNING: Caching might not be effective or query count is same.")

    print("\n--- Verifying Wishlist View (Optimization) ---")
    request = factory.get('/wishlist/')
    request.user = user
    reset_queries()
    try:
        response = wishlist_view(request)
        if response.status_code == 200:
             print(f"Wishlist View: OK, Queries: {len(connection.queries)}")
    except Exception as e:
        print(f"Wishlist View Error: {e}")

    print("\n--- Verifying Order Detail (Optimization) ---")
    if Order.objects.filter(user=user).exists():
        order = Order.objects.filter(user=user).first()
        request = factory.get(f'/orders/{order.id}/')
        request.user = user
        reset_queries()
        try:
            response = order_detail(request, order.id)
            if response.status_code == 200:
                 print(f"Order Detail View: OK, Queries: {len(connection.queries)}")
        except Exception as e:
            print(f"Order Detail Error: {e}")
    else:
        print("No orders found for test user, skipping Order Detail check.")

if __name__ == '__main__':
    verify_optimizations()
