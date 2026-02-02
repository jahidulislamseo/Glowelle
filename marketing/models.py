from django.db import models
from django.utils import timezone

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True, help_text="Case insensitive")
    discount_percent = models.IntegerField(help_text="Percentage discount (e.g., 20 for 20%)")
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

class HomeSlider(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='sliders/')
    link_url = models.URLField(blank=True, null=True, help_text="URL to redirect when clicked")
    sort_order = models.IntegerField(default=0, help_text="Low numbers appear first")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        return self.title or "Slider Image"

class DealOfTheDay(models.Model):
    title = models.CharField(max_length=255, default="Deal of the Day")
    subtitle = models.CharField(max_length=500, blank=True, null=True, help_text="e.g. Get up to 50% OFF...")
    image = models.ImageField(upload_to='deals/', help_text="Background Banner Image (Recommended: 1000x400px)")
    discount_percentage = models.IntegerField(default=0, help_text="e.g. 50")
    end_date = models.DateTimeField(help_text="Countdown will end at this time")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class SellingNote(models.Model):
    title = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=255, blank=True, null=True, help_text="e.g. On orders over ৳1000")
    icon = models.CharField(max_length=50, help_text="Lucide icon name (e.g., truck, headset, shield-check, undo-2, leaf, award)")
    sort_order = models.IntegerField(default=0, help_text="Lower numbers appear first")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order']
        verbose_name = "Selling Note"
        verbose_name_plural = "Selling Notes"

    def __str__(self):
        return self.title
