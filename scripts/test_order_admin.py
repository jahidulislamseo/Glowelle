import os
import django
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
username = 'admin_test_user'
password = 'password123'

client = Client()
client.login(username=username, password=password)

url = '/admin/orders/order/2/change/'
print(f"Fetching URL: {url}")

try:
    response = client.get(url)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✓ Page rendered successfully!")
    else:
        print("✗ Page failed to render.")
except Exception as e:
    print(f"\n{'='*60}")
    print("FULL ERROR TRACEBACK:")
    print('='*60)
    traceback.print_exc()
    print('='*60)
