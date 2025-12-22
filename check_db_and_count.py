import os
import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from products.models import Product

print(f"Active Database Engine: {settings.DATABASES['default']['ENGINE']}")
print(f"Active Database Name: {settings.DATABASES['default']['NAME']}")

count = Product.objects.count()
print(f"Product Count: {count}")
