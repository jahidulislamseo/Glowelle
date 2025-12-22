
import os
import django
from django.conf import settings
from django.test import Client
from django.urls import reverse

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User
from orders.models import Order
from decimal import Decimal

def verify_admin_ui():
    print("Verifying Admin Order UI Rendering...")
    
    # 1. Setup Admin User & Client
    username = 'verify_admin'
    password = 'password123'
    email = 'verify@admin.com'
    
    user, created = User.objects.get_or_create(username=username, email=email)
    user.set_password(password)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    
    client = Client()
    login_success = client.login(username=username, password=password)
    if login_success:
        print("[OK] Admin Login Successful")
    else:
        print("[FAIL] Admin Login Failed")
        return

    # 2. Create Dummy Order
    order = Order.objects.create(
        user=user,
        full_name="UI Test Customer",
        phone="01711111111",
        address="Test Address",
        total=Decimal("500.00"),
        source='website'
    )
    # Ensure reference matches what we expect or just use ID
    print(f"[OK] Test Order Created: #{order.id}")

    # 3. Request Admin Change Page
    # URL pattern name for admin change view is usually 'admin:<app_label>_<model_name>_change'
    url = reverse('admin:orders_order_change', args=[order.id])
    print(f"Requesting URL: {url}")
    
    try:
        response = client.get(url)
        
        # 4. Checks
        if response.status_code == 200:
            print("[OK] Page Load (Status 200)")
        else:
            print(f"[FAIL] Page Load Status: {response.status_code}")
            return

        content = response.content.decode('utf-8')
        
        # Check for Custom Template Elements
        checks = [
            ("oms-container", "Main Dashboard Container"),
            ("oms-card", "Dashboard Cards"),
            ("Order Timeline", "Timeline Section"),
            ("Customer Info", "Customer Sidebar"),
            ("Delivery & Logistics", "Logistics Section"),
            ("Product Details", "Products Section"),
            (f"#{order.order_reference}", "Order Reference Display"),
        ]
        
        for signature, name in checks:
            if signature in content:
                print(f"[OK] Found Element: {name}")
            else:
                print(f"[FAIL] Missing Element: {name}")
                if "error" in content.lower():
                     print("   -> Possible Error in template found.")

    except Exception as e:
        print(f"[FAIL] Exception during request: {e}")

if __name__ == "__main__":
    verify_admin_ui()
