from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from core.models import SEOModel

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
    description = models.TextField(null=True, blank=True)
    price = models.FloatField(db_index=True)
    original_price = models.FloatField(null=True, blank=True)
    image = models.ImageField(upload_to='products/main/', max_length=255, blank=True, null=True)
    # images field replaced by ProductImage model 
    rating = models.FloatField(default=0)
    reviews_count = models.IntegerField(default=0)
    in_stock = models.BooleanField(default=True, db_index=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_new = models.BooleanField(default=False)
    is_best_seller = models.BooleanField(default=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.image:
            from PIL import Image
            import os
            
            try:
                img_path = self.image.path
                if os.path.exists(img_path):
                    with Image.open(img_path) as img:
                        if img.height > 1024 or img.width > 1024:
                            output_size = (1024, 1024)
                            img.thumbnail(output_size)
                            img.save(img_path, quality=85, optimize=True)
            except Exception as e:
                # Log error or silently fail to avoid crashing if image is corrupted
                print(f"Error resizing image for product {self.id}: {e}")

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
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.title}"

class Wishlist(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.title}"
