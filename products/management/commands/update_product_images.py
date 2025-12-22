from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = 'Update product images from imported media files'

    def handle(self, *args, **kwargs):
        # slug_keyword -> image_prefix mapping
        mapping = {
            'premium-beef': 'beef',
            'fresh-carrots': 'carrots',
            'deshi-chicken': 'chicken',
            'potato-chips': 'chips',
            'padma-hilsa': 'fish', 
            'fresh-juice': 'juice',
            'fresh-milk': 'milk',
            'fresh-onions': 'onions',
            'organic-potatoes': 'potatoes',
            'herbal-shampoo': 'shampoo',
            'fresh-tomatoes': 'tomatoes',
        }

        for slug, img_prefix in mapping.items():
            try:
                product = Product.objects.get(slug=slug)
                main_img = f'/media/products/{img_prefix}-1.png'
                secondary_img = f'/media/products/{img_prefix}-2.png'

                # Update Main Image
                product.image = main_img
                
                # Update Gallery (JSONField)
                product.images = [main_img, secondary_img]
                
                product.save()
                
                self.stdout.write(self.style.SUCCESS(f'Updated images for {slug}'))

            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Product not found: {slug}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error updating {slug}: {str(e)}'))
