import json
from django.core.management.base import BaseCommand
from products.models import Product, Category
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Import products from JSON file'

    def handle(self, *args, **kwargs):
        with open('products.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.stdout.write(f"Found {len(data)} products in JSON")

        for item in data:
            # Handle Category
            cat_data = item.get('category')
            if cat_data:
                category, _ = Category.objects.get_or_create(
                    slug=cat_data.get('slug'),
                    defaults={
                        'name': cat_data.get('name'),
                        'icon': cat_data.get('icon', '📦')
                    }
                )
            else:
                category, _ = Category.objects.get_or_create(name='Uncategorized', slug='uncategorized')

            # Handle Product
            # Some prices might be null/None in raw data
            price = item.get('price') or 0
            original_price = item.get('originalPrice')
            
            # Map 'images' array to 'json_images' if using Postgres/JSONField, 
            # or just take the first one as main image
            images_list = item.get('images', [])
            main_image = item.get('image') or (images_list[0] if images_list else '')

            product, created = Product.objects.update_or_create(
                slug=item.get('slug'),
                defaults={
                    'title': item.get('title'),
                    'description': item.get('description', ''),
                    'price': price,
                    'original_price': original_price,
                    'image': main_image,
                    'images': images_list, # JSONField
                    'category': category,
                    'rating': item.get('rating', 0.0),
                    'reviews_count': item.get('reviewsCount', 0),
                    'in_stock': item.get('inStock', True),
                    'is_new': item.get('isNew', False),
                    'is_best_seller': item.get('isBestSeller', False),
                }
            )
            
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action}: {product.title}")

        self.stdout.write(self.style.SUCCESS(f'Successfully processing {len(data)} products'))
