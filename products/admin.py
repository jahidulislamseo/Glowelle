from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import redirect
from .models import Category, Product, Review, Wishlist, Brand, ProductVariant, StockLog, ProductImage, ProductVideo
from import_export.admin import ImportExportModelAdmin
from core.admin_mixins import ChangeHistoryMixin

@admin.register(Brand)
class BrandAdmin(ChangeHistoryMixin, admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

@admin.register(Category)
class CategoryAdmin(ChangeHistoryMixin, admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'image', 'icon')
        }),
        ('SEO Settings', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords', 'og_image'),
            'classes': ('collapse',),
        }),
    )

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    extra = 1

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

class LowStockFilter(admin.SimpleListFilter):
    title = 'Stock Status'
    parameter_name = 'stock_status'

    def lookups(self, request, model_admin):
        return (
            ('low', 'Low Stock (< 10)'),
            ('out', 'Out of Stock (0)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'low':
            return queryset.filter(stock_quantity__lt=10, stock_quantity__gt=0)
        if self.value() == 'out':
            return queryset.filter(stock_quantity=0)

@admin.register(Product)
class ProductAdmin(ChangeHistoryMixin, admin.ModelAdmin):
    list_display = ['title', 'price', 'in_stock', 'stock_quantity', 'category', 'brand', 'display_image', 'rating', 'chatbot_priority_badge']
    list_display_links = ['title']
    list_filter = ['category', 'brand', LowStockFilter, 'in_stock', 'is_new', 'is_best_seller', 'chatbot_priority']
    search_fields = ['title', 'description', 'sku']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProductImageInline, ProductVideoInline, ProductVariantInline]
    actions = ['make_out_of_stock', 'add_stock_10', 'enable_chatbot_priority', 'disable_chatbot_priority']

    # Optimization
    list_select_related = ['category', 'brand']
    autocomplete_fields = ['category', 'brand']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:product_id>/toggle-chatbot-priority/',
                self.admin_site.admin_view(self.toggle_chatbot_priority_view),
                name='products_product_toggle_chatbot_priority',
            ),
        ]
        return custom_urls + urls

    def toggle_chatbot_priority_view(self, request, product_id):
        product = Product.objects.get(pk=product_id)
        product.chatbot_priority = not product.chatbot_priority
        product.save()
        status = "✅ চালু" if product.chatbot_priority else "❌ বন্ধ"
        self.message_user(request, f'"{product.title}" — Chatbot Priority {status} করা হয়েছে।')
        return redirect(request.META.get('HTTP_REFERER', reverse('admin:products_product_changelist')))

    def chatbot_priority_badge(self, obj):
        toggle_url = reverse('admin:products_product_toggle_chatbot_priority', args=[obj.pk])
        if obj.chatbot_priority:
            return format_html(
                '<a href="{}" title="Click to disable" style="'
                'display:inline-block; padding:4px 14px; border-radius:20px;'
                'background:#28a745; color:#fff; font-size:12px; font-weight:600;'
                'text-decoration:none; letter-spacing:0.3px;">'
                '✓ Active</a>',
                toggle_url
            )
        return format_html(
            '<a href="{}" title="Click to enable" style="'
            'display:inline-block; padding:4px 14px; border-radius:20px;'
            'background:#e9ecef; color:#6c757d; font-size:12px; font-weight:600;'
            'text-decoration:none; border:1px solid #dee2e6; letter-spacing:0.3px;">'
            '✗ Off</a>',
            toggle_url
        )
    chatbot_priority_badge.short_description = "Chatbot Priority"

    def make_out_of_stock(self, request, queryset):
        updated = queryset.update(stock_quantity=0, in_stock=False)
        self.message_user(request, f"{updated} products marked as out of stock.")
    make_out_of_stock.short_description = "Mark selected products as Out of Stock"

    def add_stock_10(self, request, queryset):
        from django.db.models import F
        updated = queryset.update(stock_quantity=F('stock_quantity') + 10, in_stock=True)
        self.message_user(request, f"{updated} products stock increased by 10.")
    add_stock_10.short_description = "Add 10 units to stock"

    def enable_chatbot_priority(self, request, queryset):
        updated = queryset.update(chatbot_priority=True)
        self.message_user(request, f"{updated} products chatbot priority চালু করা হয়েছে।")
    enable_chatbot_priority.short_description = "✅ Chatbot Priority চালু করো"

    def disable_chatbot_priority(self, request, queryset):
        updated = queryset.update(chatbot_priority=False)
        self.message_user(request, f"{updated} products chatbot priority বন্ধ করা হয়েছে।")
    disable_chatbot_priority.short_description = "❌ Chatbot Priority বন্ধ করো"
    
    fieldsets = (
        ('General Information', {
            'fields': ('title', 'slug', 'category', 'brand', 'short_description', 'description', 'price', 'original_price', 'image')
        }),
        ('Status & Visibility', {
            'fields': ('in_stock', 'stock_quantity', 'is_new', 'is_best_seller', 'chatbot_priority')
        }),
        ('SEO Settings', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords', 'og_image'),
            'classes': ('collapse',),
        }),
    )
    
    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />', obj.display_image_url)
        return "-"
    display_image.short_description = "Image"

@admin.register(StockLog)
class StockLogAdmin(admin.ModelAdmin):
    list_display = ['product', 'variant', 'quantity', 'reason', 'created_by', 'created_at']
    list_filter = ['reason', 'created_at']
    search_fields = ['product__title', 'reason']
    readonly_fields = ['product', 'variant', 'quantity', 'reason', 'created_by', 'created_at']
    
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'created_at']
    list_filter = ['rating']

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
