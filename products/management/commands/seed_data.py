from django.core.management.base import BaseCommand
from products.models import Category, Product, ProductImage
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Seeds the database with initial data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')

        # Categories
        categories_data = [
            {'name': 'Fruits', 'slug': 'fruits', 'icon': '🍎'},
            {'name': 'Vegetables', 'slug': 'vegetables', 'icon': '🥦'},
            {'name': 'Meat & Fish', 'slug': 'meat-fish', 'icon': '🍖'},
            {'name': 'Snacks', 'slug': 'snacks', 'icon': '🍪'},
            {'name': 'Dairy', 'slug': 'dairy', 'icon': '🥛'},
            {'name': 'Beverages', 'slug': 'beverages', 'icon': '🥤'},
        ]

        for cat_data in categories_data:
            Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
        
        self.stdout.write(f'Created {len(categories_data)} categories.')

        # Products (Sample Data matching Next.js)
        products_data = [
            {
                'title': 'Organic Bananas',
                'slug': 'organic-bananas-new', # New slug to avoid conflict if rerun
                'category_slug': 'fruits',
                'price': 120,
                'original_price': 150,
                'image': 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=800&q=80',
                'images': [
                    'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=800&q=80',
                    'https://images.unsplash.com/photo-1587334274328-64186a80aeee?w=800&q=80'
                ],
                'description': 'Fresh organic bananas, rich in potassium.',
                'rating': 4.5,
                'reviews_count': 120,
                'in_stock': True,
                'is_new': True
            },
            {
                'title': 'Red Tomato',
                'slug': 'red-tomato',
                'category_slug': 'vegetables',
                'price': 80,
                'original_price': 100,
                'image': 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=800&q=80',
                'images': ['https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=800&q=80'],
                'description': 'Fresh red tomatoes from local farm.',
                'rating': 4.3,
                'reviews_count': 85,
                'in_stock': True,
                'is_best_seller': True
            },
            {
                'title': 'Fresh Beef',
                'slug': 'fresh-beef',
                'category_slug': 'meat-fish',
                'price': 750,
                'original_price': 800,
                'image': 'https://images.unsplash.com/photo-1603048297172-c92544798d5e?w=800&q=80',
                'images': ['https://images.unsplash.com/photo-1603048297172-c92544798d5e?w=800&q=80'],
                'description': 'Premium quality fresh beef.',
                'rating': 4.8,
                'reviews_count': 200,
                'in_stock': True,
                'is_best_seller': True
            }
        ]

        for p_data in products_data:
            cat_slug = p_data.pop('category_slug')
            extra_images = p_data.pop('images', [])
            category = Category.objects.get(slug=cat_slug)
            
            product, created = Product.objects.update_or_create(
                slug=p_data['slug'],
                defaults={
                    **p_data,
                    'category': category
                }
            )

            for img_url in extra_images:
                ProductImage.objects.get_or_create(
                    product=product,
                    image=img_url,
                    defaults={'alt_text': product.title}
                )

        self.stdout.write(f'Seeded {len(products_data)} products.')
