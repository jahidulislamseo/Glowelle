
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from orders.models import Order
from django.urls import reverse
from django.contrib.auth import get_user_model

try:
    order = Order.objects.get(id=4)
    print(f"Order ID: {order.id}")
    print(f"User: {order.user}")
    if order.user:
        print(f"User ID: {order.user.id}, Type: {type(order.user.id)}")
        print(f"User PK: {order.user.pk}, Type: {type(order.user.pk)}")
    else:
        print("Order has no user.")

    # Try reversing manually
    if order.user:
        try:
            url = reverse("admin:users_user_change", args=[order.user.id])
            print(f"Reverse Success: {url}")
        except Exception as e:
            print(f"Reverse Failed with ID: {e}")

    try:
        url_dummy = reverse("admin:users_user_change", args=[1])
        print(f"Reverse Dummy(1) Success: {url_dummy}")
    except Exception as e:
        print(f"Reverse Dummy(1) Failed: {e}")

except Order.DoesNotExist:
    print("Order #4 not found.")
except Exception as e:
    print(f"Error: {e}")
