import os
import django
import sys
import random
from datetime import timedelta
from django.utils import timezone

sys.path.append(os.path.abspath('c:/Users/Jahidul-islam/Desktop/all apk and website/al-barakah-mart-django'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from analytics.models import VisitorSession, AnalyticsEvent, PageView
from users.models import User
from orders.models import Order
from marketing.models import Coupon # Ensure this exists, otherwise skip

# 1. Create Sessions
print("Creating Sessions...")
users = User.objects.all()
if not users.exists():
    user = User.objects.create_user('testuser', 'test@example.com', 'password')
    users = [user]

for i in range(20):
    session = VisitorSession.objects.create(
        session_key=f"seed_session_{random.randint(1000,99999)}",
        user=random.choice(users) if random.random() > 0.5 else None,
        ip_address=f"192.168.1.{random.randint(1, 255)}",
        device_type=random.choice(['mobile', 'desktop', 'tablet']),
        os=random.choice(['Windows', 'iOS', 'Android', 'MacOS']),
        browser=random.choice(['Chrome', 'Firefox', 'Safari']),
        is_bounce=random.choice([True, False])
    )
    # Set time to past
    session.start_time = timezone.now() - timedelta(days=random.randint(0, 30))
    session.save()
    
    # 2. Add Events
    events = [
        ('wishlist_add', 'Product 1'),
        ('remove_from_cart', 'Product 2'),
        ('coupon_used', 'SAVE10'),
        ('payment_failed', 'Insufficient Funds'),
        ('out_of_stock_click', 'Product 5'),
        ('logout', 'User Logout'),
        ('search', 'Organic Honey'),
        ('search', 'Dates'),
        ('add_to_cart', 'Product 3'),
        ('checkout_start', 'Cart'),
        ('error_404', '/unknown-page')
    ]
    
    # Randomly assign events
    num_events = random.randint(1, 5)
    for _ in range(num_events):
        evt_type, val = random.choice(events)
        AnalyticsEvent.objects.create(
            session=session,
            user=session.user,
            event_type=evt_type,
            value=val,
            timestamp=session.start_time + timedelta(minutes=random.randint(1, 10))
        )

print("Seeding Complete.")
