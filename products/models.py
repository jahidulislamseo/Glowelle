import os

from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from core.models import SEOModel


DEFAULT_PRODUCT_IMAGE_URL = 'https://placehold.co/600x600?text=No+Image&format=webp'


def ensure_webp_url(image_field):
    if not image_field:
        return DEFAULT_PRODUCT_IMAGE_URL

    # If the image name itself is a URL, return it directly
    if image_field.name and image_field.name.startswith(('http://', 'https://')):
        return image_field.name

    image_url = image_field.url
    if image_url.startswith(('http://', 'https://')):
        return image_url

    try:
        image_path = image_field.path
    except Exception:
        return image_url

    if not os.path.exists(image_path):
        return image_url


    base_path, ext = os.path.splitext(image_path)
    webp_path = f"{base_path}.webp"
    webp_url = f"{os.path.splitext(image_url)[0]}.webp"

    if os.path.exists(webp_path):
        return webp_url

    try:
        from PIL import Image

        with Image.open(image_path) as img:
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
            img.save(webp_path, 'WEBP', quality=85, optimize=True, method=6)
        return webp_url
    except Exception as e:
        # Fallback to original URL when WebP conversion fails
        print(f"Error creating WebP for {image_field}: {e}")
        return image_url

class Category(SEOModel):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop') + f'?category={self.slug}'

class Brand(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to='brands', null=True, blank=True)

    def __str__(self):
        return self.name

class Product(SEOModel):
    title = models.CharField(max_length=500)
    slug = models.SlugField(unique=True)
    short_description = models.TextField(max_length=500, null=True, blank=True, help_text="Short summary of the product (300-500 chars)")
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, db_index=True)
    original_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='products/main/', max_length=255, blank=True, null=True)
    # images field replaced by ProductImage model 
    rating = models.FloatField(default=0)
    reviews_count = models.IntegerField(default=0)
    in_stock = models.BooleanField(default=True, db_index=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_new = models.BooleanField(default=False)
    is_best_seller = models.BooleanField(default=False)
    chatbot_priority = models.BooleanField(default=False, help_text="Prioritize this product in chatbot responses")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['category', '-created_at'], name='prod_cat_created_idx'),
            models.Index(fields=['category', 'price'], name='prod_cat_price_idx'),
            models.Index(fields=['is_best_seller', '-created_at'], name='prod_bestseller_idx'),
            models.Index(fields=['-created_at', 'in_stock'], name='prod_created_stock_idx'),
            models.Index(fields=['in_stock', 'category'], name='prod_stock_cat_idx'),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])

    @property
    def discount_percent(self):
        if self.original_price and self.original_price > self.price:
            return round((self.original_price - self.price) / self.original_price * 100)
        return None

    @property
    def savings_amount(self):
        if self.original_price and self.original_price > self.price:
            return int(self.original_price - self.price)
        return None

    @property
    def display_image_url(self):
        if not self.image:
            return DEFAULT_PRODUCT_IMAGE_URL

        return ensure_webp_url(self.image)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.image:
            try:
                from PIL import Image

                img_path = self.image.path
                if os.path.exists(img_path):
                    with Image.open(img_path) as img:
                        if img.height > 1024 or img.width > 1024:
                            output_size = (1024, 1024)
                            img.thumbnail(output_size)
                            img.save(img_path, quality=85, optimize=True)
            except Exception as e:
                print(f"Error resizing image for product {self.id}: {e}")

            ensure_webp_url(self.image)

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.product.title} - {self.size}/{self.color}"

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='additional_images')
    image = models.ImageField(upload_to='products/extra/')
    alt_text = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Image for {self.product.title}"

    @property
    def display_image_url(self):
        if not self.image:
            return DEFAULT_PRODUCT_IMAGE_URL

        return ensure_webp_url(self.image)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            ensure_webp_url(self.image)

class ProductVideo(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='videos')
    video = models.FileField(upload_to='products/videos/')
    title = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Video for {self.product.title}"

class StockLog(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_logs')
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_logs')
    quantity = models.IntegerField(help_text="Positive for addition, negative for deduction")
    reason = models.CharField(max_length=255, default="Manual Adjustment")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.product.title} - {self.quantity} ({self.reason})"

class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    comment = models.TextField()
    image = models.ImageField(upload_to='reviews/', null=True, blank=True)
    is_verified_purchase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.title} ({self.rating}★)"

class StockAlert(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='stock_alerts')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_alerts')
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_alerts')
    email = models.EmailField(null=True, blank=True, help_text="Email for notification if user is guest (optional)")
    is_notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product', 'variant')

    def __str__(self):
        return f"Alert for {self.user.username} - {self.product.title}"

class Wishlist(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.title}"
