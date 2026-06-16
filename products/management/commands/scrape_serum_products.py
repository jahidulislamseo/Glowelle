"""
Management command to scrape 50 serum products from choicelegacy.com.bd
and import them into the Django database.

Usage:
    python manage.py scrape_serum_products
    python manage.py scrape_serum_products --no-images   # skip image downloads
    python manage.py scrape_serum_products --update      # update existing products
"""

import io
import os
import time
import urllib.parse
import urllib.request

import requests
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from products.models import Brand, Category, Product, ProductImage


SHOPIFY_JSON_URL = "https://choicelegacy.com.bd/collections/serum/products.json?limit=50"
PRODUCT_BASE_URL = "https://choicelegacy.com.bd/products/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


class Command(BaseCommand):
    help = "Scrape 50 serum products from choicelegacy.com.bd and import into database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-images",
            action="store_true",
            help="Skip downloading product images (faster import)",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="Update existing products (by slug) instead of skipping them",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum number of products to import (default: 50)",
        )

    def handle(self, *args, **options):
        download_images = not options["no_images"]
        update_existing = options["update"]
        limit = options["limit"]

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\n{'='*60}\n  Serum Product Scraper — choicelegacy.com.bd\n{'='*60}"
        ))
        self.stdout.write(f"  Settings: download_images={download_images}, update={update_existing}, limit={limit}\n")

        # ── Step 1: Fetch products from Shopify JSON API ──────────────────────
        self.stdout.write("\n[1/3] Fetching products from Shopify API...")
        products_data = self._fetch_products(limit)
        if not products_data:
            self.stdout.write(self.style.ERROR("No products fetched. Aborting."))
            return
        self.stdout.write(self.style.SUCCESS(f"  ✓ Fetched {len(products_data)} products"))

        # ── Step 2: Ensure 'Serum' category exists ────────────────────────────
        self.stdout.write("\n[2/3] Setting up Serum category...")
        serum_category = self._get_or_create_category()
        self.stdout.write(self.style.SUCCESS(f"  ✓ Category ready: {serum_category.name}"))

        # ── Step 3: Import each product ───────────────────────────────────────
        self.stdout.write(f"\n[3/3] Importing {len(products_data)} products...\n")

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for idx, p in enumerate(products_data, start=1):
            title = p.get("title", "").strip()
            handle = p.get("handle", "").strip()
            vendor = p.get("vendor", "").strip()
            product_type = p.get("product_type", "Serum")
            body_html = p.get("body_html", "") or ""
            images = p.get("images", [])
            variants = p.get("variants", [])

            # Build unique slug from handle
            slug = slugify(handle)[:200] if handle else slugify(title)[:200]

            # Price from first variant
            price = 0.0
            original_price = None
            if variants:
                first_variant = variants[0]
                try:
                    price = float(first_variant.get("price") or 0)
                except (ValueError, TypeError):
                    price = 0.0
                try:
                    compare = first_variant.get("compare_at_price")
                    original_price = float(compare) if compare else None
                except (ValueError, TypeError):
                    original_price = None

            # Check stock across all variants
            in_stock = any(
                v.get("available", True) for v in variants
            ) if variants else True

            # ── Brand ────────────────────────────────────────────────────────
            brand = None
            if vendor:
                brand_slug = slugify(vendor)[:200]
                brand, _ = Brand.objects.get_or_create(
                    slug=brand_slug,
                    defaults={"name": vendor}
                )

            # ── Check if product already exists ──────────────────────────────
            existing = Product.objects.filter(slug=slug).first()
            if existing and not update_existing:
                self.stdout.write(f"  [{idx:02d}] SKIP  — {title[:60]}")
                skipped_count += 1
                continue

            # ── Clean description ─────────────────────────────────────────────
            # Strip HTML tags for short_description
            import re
            clean_desc = re.sub(r"<[^>]+>", " ", body_html).strip()
            clean_desc = re.sub(r"\s+", " ", clean_desc)
            short_desc = clean_desc[:490] if clean_desc else f"{title} — Premium skincare serum."

            # ── Create or update product ──────────────────────────────────────
            product_data = {
                "title": title,
                "short_description": short_desc,
                "description": body_html,
                "price": price if price > 0 else 0.01,
                "original_price": original_price,
                "in_stock": in_stock,
                "stock_quantity": 10 if in_stock else 0,
                "category": serum_category,
                "brand": brand,
                "is_new": True,
                "rating": 4.5,
                "reviews_count": 0,
            }

            if existing and update_existing:
                for field, value in product_data.items():
                    setattr(existing, field, value)
                existing.save()
                product = existing
                updated_count += 1
                action = "UPDATE"
            else:
                product = Product.objects.create(slug=slug, **product_data)
                created_count += 1
                action = "CREATE"

            # ── Assign Shopify CDN Image URLs directly ────────────────────────
            if images:
                main_img_url = images[0].get("src", "")
                if main_img_url:
                    product.image.name = main_img_url
                    img_status = "🔗 (CDN)"
                else:
                    img_status = "—"
            else:
                img_status = "—"

            product.save()

            # ── Additional Images as CDN URLs ─────────────────────────────────
            if len(images) > 1:
                if existing and update_existing:
                    ProductImage.objects.filter(product=product).delete()

                extra_imgs = images[1:4]  # limit to 3 extra images
                for extra_img in extra_imgs:
                    extra_url = extra_img.get("src", "")
                    if extra_url:
                        ProductImage.objects.create(
                            product=product,
                            image=extra_url
                        )


            self.stdout.write(
                f"  [{idx:02d}] {action:<6} {img_status}  {title[:55]}"
                f"  | BDT {price:.0f}"
                f"  | {vendor}"
            )

            # Small delay to be polite to the server
            time.sleep(0.3)

        # ── Summary ───────────────────────────────────────────────────────────
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.SUCCESS(f"  ✅ DONE!"))
        self.stdout.write(f"  Created : {created_count}")
        self.stdout.write(f"  Updated : {updated_count}")
        self.stdout.write(f"  Skipped : {skipped_count}")
        self.stdout.write(f"  Total   : {created_count + updated_count + skipped_count}")
        self.stdout.write(f"{'='*60}\n")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _fetch_products(self, limit):
        """Fetch products from Shopify JSON API."""
        url = f"https://choicelegacy.com.bd/collections/serum/products.json?limit={limit}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            return data.get("products", [])
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  API request failed: {e}"))
            return []

    def _get_or_create_category(self):
        """Get or create the Serum category."""
        category, created = Category.objects.get_or_create(
            slug="serum",
            defaults={
                "name": "Serum",
                "icon": "💧",
            }
        )
        if created:
            self.stdout.write(f"  Created new category: Serum")
        else:
            self.stdout.write(f"  Using existing category: {category.name}")
        return category

    def _download_image(self, url):
        """Download an image from a URL and return a Django File object."""
        try:
            # Remove Shopify CDN query parameters that might cause issues
            clean_url = url.split("?")[0]
            # Keep the version query param for Shopify but skip others
            if "v=" in url:
                clean_url = url  # keep v= param for Shopify CDN

            req = urllib.request.Request(clean_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as response:
                data = response.read()

            if not data:
                return None

            parsed = urllib.parse.urlparse(clean_url)
            filename = os.path.basename(parsed.path) or "image.jpg"
            if not os.path.splitext(filename)[1]:
                filename += ".jpg"

            return File(io.BytesIO(data), name=filename)

        except Exception as e:
            self.stdout.write(self.style.WARNING(f"    Download failed ({url[:60]}...): {e}"))
            return None
