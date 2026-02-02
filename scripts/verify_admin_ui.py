
import os
import django
from django.conf import settings
from django.test import Client, RequestFactory
from django.urls import reverse
from django.contrib.admin.sites import site

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User
from orders.models import Order
from orders.admin import OrderAdmin
from decimal import Decimal

def verify_admin_ui():
    print("Verifying Admin Order UI Rendering (Deep Check)...")
    
    # 1. Setup Admin User
    username = 'verify_admin'
    
    user, created = User.objects.get_or_create(username=username, email='verify@admin.com')
    if created:
        user.set_password('password123')
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print("Created admin user")

    # 2. Get/Create Order
    order = Order.objects.first()
    if not order:
        order = Order.objects.create(
            user=user, 
            full_name="Test", 
            total=Decimal("100"), 
            source='admin'
        )
        print("Created test order")
    else:
        print(f"Using existing order #{order.id}")

    # 3. Simulate Request directly to ModelAdmin (Bypassing Middleware Host Checks if possible)
    factory = RequestFactory()
    url = reverse('admin:orders_order_change', args=[order.id])
    request = factory.get(url)
    request.user = user
    
    # Instantiate Admin
    model_admin = OrderAdmin(Order, site)
    
    print(f"Testing URL: {url}")
    
    try:
        # Call change_view directly
        response = model_admin.change_view(request, str(order.id))
        
        # Check if response is a TemplateResponse (rendering hasn't happened yet)
        if hasattr(response, 'render'):
            response.render()
            
        print(f"[OK] Response Status: {response.status_code}")
        
        content = response.content.decode('utf-8')
        
        if response.status_code == 200:
            print("[OK] Page Rendered Successfully")
            if "oms-container" in content:
                print("[OK] Dashboard UI Found")
            else:
                 print("[WARN] Dashboard UI container NOT found. Are templates loading?")
        else:
            print(f"[FAIL] Error Status. Content snippet: {content[:500]}")
            
    except Exception as e:
        import traceback
        print("[CRITICAL FAIL] Exception during view rendering:")
        traceback.print_exc()

if __name__ == "__main__":
    verify_admin_ui()
