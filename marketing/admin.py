from django.contrib import admin
from django.utils.html import format_html
from .models import Coupon, HomeSlider

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percent', 'valid_from', 'valid_to', 'active']
    list_filter = ['active', 'valid_to']
    search_fields = ['code']

@admin.register(HomeSlider)
class HomeSliderAdmin(admin.ModelAdmin):
    list_display = ['title', 'display_image', 'sort_order', 'is_active', 'link_url']
    list_editable = ['sort_order', 'is_active']
    search_fields = ['title']

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 120px; height: 50px; object-fit: cover; border-radius: 4px;" />', obj.image.url)
        return "-"
    display_image.short_description = "Preview"
