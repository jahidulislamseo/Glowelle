import io
import json
import os
import urllib.request
import urllib.parse

from django.core.files import File
from django.core.management.base import BaseCommand

from products.models import Product, ProductImage

DEFAULT_IMAGE_MAPPING = {
    # Example mapping. Replace the URLs with real image URLs as needed.
    # 'premium-beef': {
    #     'main': 'https://example.com/images/beef-main.webp',
    #     'additional': [
    #         'https://example.com/images/beef-1.webp',
    #         'https://example.com/images/beef-2.webp',
    #     ],
    # },
}


class Command(BaseCommand):
    help = 'Download product images from remote URLs and assign them to Product records.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mapping-file',
            type=str,
            help='JSON file with slug -> {main, additional} image URL mapping.',
        )

        parser.add_argument(
            '--clear-additional',
            action='store_true',
            help='Remove existing additional images before importing new ones.',
        )

        parser.add_argument(
            '--fill-missing',
            action='store_true',
            help='Generate placeholder images for products with missing or broken main images.',
        )

    def handle(self, *args, **options):
        mapping_file = options.get('mapping_file')
        clear_additional = options.get('clear_additional')

        fill_missing = options.get('fill_missing')

        if mapping_file:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
        else:
            mapping = DEFAULT_IMAGE_MAPPING

        if not mapping and not fill_missing:
            self.stdout.write(self.style.WARNING('No image mapping provided.'))
            self.stdout.write(self.style.WARNING('Create a JSON mapping file or update DEFAULT_IMAGE_MAPPING.'))
            return

        if fill_missing:
            self.fill_missing_images(clear_additional)
            return

        for slug, urls in mapping.items():
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Product not found: {slug}'))
                continue

            if clear_additional:
                ProductImage.objects.filter(product=product).delete()

            main_url = urls.get('main')
            additional_urls = urls.get('additional', [])

            if main_url:
                main_file = self.download_remote_image(main_url)
                if main_file:
                    product.image.save(main_file.name, main_file, save=False)
                    self.stdout.write(self.style.SUCCESS(f'Updated main image for {slug}'))

            for image_url in additional_urls:
                img_file = self.download_remote_image(image_url)
                if not img_file:
                    continue

                ProductImage.objects.create(product=product, image=img_file)
                self.stdout.write(self.style.SUCCESS(f'Added additional image for {slug}: {image_url}'))

            product.save()

        self.stdout.write(self.style.SUCCESS('Product image download complete.'))

    def fill_missing_images(self, clear_additional):
        products = Product.objects.all()
        filled = 0
        for product in products:
            if self.product_has_valid_image(product):
                continue

            placeholder_url = self.placeholder_image_url(product)
            image_file = self.download_remote_image(placeholder_url)
            if image_file:
                filename = f'placeholder-{product.slug}.webp'
                product.image.save(filename, image_file, save=False)
                product.save()
                filled += 1
                self.stdout.write(self.style.SUCCESS(f'Filled placeholder image for {product.slug}'))

        self.stdout.write(self.style.SUCCESS(f'Filled {filled} missing product images.'))

    def product_has_valid_image(self, product):
        if not product.image:
            return False

        try:
            return os.path.exists(product.image.path)
        except Exception:
            return False

    def placeholder_image_url(self, product):
        text = urllib.parse.quote_plus(product.title[:40])
        return f'https://placehold.co/600x600?text={text}&format=webp&bg=efefef&fg=777'

    def download_remote_image(self, url):
        try:
            response = urllib.request.urlopen(url)
            data = response.read()
            parsed = urllib.parse.urlparse(url)
            filename = os.path.basename(parsed.path) or 'image'
            if not os.path.splitext(filename)[1]:
                filename += '.jpg'

            image_file = io.BytesIO(data)
            return File(image_file, name=filename)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to download {url}: {e}'))
            return None
