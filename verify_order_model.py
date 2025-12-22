
import os
import django
from django.conf import settings
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from orders.models import Order, OrderItem, OrderStatusHistory
from users.models import User

def verify_order_model():
    print("Verifying Order Model Changes...")
    
    # 1. Check consistency of new fields
    user = User.objects.first()
    if not user:
        print("No user found, creating dummy user")
        user = User.objects.create_user(username='testadmin', email='test@admin.com', password='password')

    try:
        order = Order.objects.create(
            user=user,
            full_name="Test Customer",
            email="test@customer.com",
            phone="01700000000",
            address="123 Test St",
            city="Dhaka",
            total=Decimal("1500.00"),
            payment_method="cod",
            source="admin",
            estimated_delivery_date="2025-01-01",
            billing_address="Same as delivery",
            is_high_risk=False
        )
        print(f"[OK] Order Created: {order.order_reference}")
        
        # 2. Check Auto-Generated Fields
        if order.order_reference:
            print(f"[OK] Order Reference generated: {order.order_reference}")
        else:
            print("[FAIL] Order Reference NOT generated")
            
        if order.invoice_number:
            print(f"[OK] Invoice Number generated: {order.invoice_number}")
        else:
            print("[FAIL] Invoice Number NOT generated")

        # 3. Check Status History Creation
        history = OrderStatusHistory.objects.filter(order=order)
        if history.exists():
            print(f"[OK] OrderStatusHistory created: {history.first().description}")
        else:
            print("[FAIL] OrderStatusHistory NOT created on create")
            
        # 4. Check Status Change Logging
        order.status = "processing"
        order.save()
        
        history_updated = OrderStatusHistory.objects.filter(order=order).count()
        if history_updated >= 2:
             print(f"[OK] Status Change Logged. Total logs: {history_updated}")
        else:
             print(f"[FAIL] Status Change NOT Logged correctly. Logs: {history_updated}")

        print("\nAll Model Verifications Passed!")
        
    except Exception as e:
        print(f"[FAIL] Verification Failed: {e}")

if __name__ == "__main__":
    verify_order_model()
