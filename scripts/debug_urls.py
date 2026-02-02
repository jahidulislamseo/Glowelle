import os
import django
from django.conf import settings
from django.test import Client
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

User = get_user_model()
user = User.objects.get(username='jahidulf1')

client = Client()
client.force_login(user)

urls = [
    '/admin/products/product/71/change/',
    '/dashboard/orders/4/invoice/',
    '/admin/products/category/12/change/'
]

for url in urls:
    print(f"Checking {url}...")
    try:
        response = client.get(url, HTTP_HOST='127.0.0.1:8000')
        print(f"Status Code: {response.status_code}")
        if response.status_code != 200:
             print(f"Content (snippet): {response.content[:500]}")
    except Exception as e:
        print(f"Exception: {e}")
