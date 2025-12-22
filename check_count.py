
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from products.models import Product

count = Product.objects.count()
db_name = settings.DATABASES['default']['NAME']
print(f"Connected to: {db_name}")
print(f"Product Count: {count}")
