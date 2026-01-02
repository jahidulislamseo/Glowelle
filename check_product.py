import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from products.models import Product

slug = "premium-beef-cuts"
try:
    product = Product.objects.get(slug=slug)
    print(f"Product found: {product.title} (ID: {product.id})")
except Product.DoesNotExist:
    print(f"Product with slug '{slug}' NOT FOUND.")
    
    print("\nAvailable products:")
    for p in Product.objects.all().order_by('-id')[:10]:
        print(f" - {p.title}: {p.slug}")
