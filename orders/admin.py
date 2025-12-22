from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Order, OrderItem, Courier, PaymentGateway
from import_export.admin import ImportExportModelAdmin

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price']

@admin.register(Courier)
class CourierAdmin(admin.ModelAdmin):
    list_display = ['name', 'website']
    search_fields = ['name']

@admin.register(PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_number', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(Order)
class OrderAdmin(ImportExportModelAdmin):
    list_display = ['id', 'user_link', 'status', 'total_display', 'items_count', 'products_list', 'payment_method', 'created_at', 'invoice_actions']
    list_editable = ['status']
    list_filter = ['status', 'payment_method', 'created_at', 'courier']
    search_fields = ['id', 'user__username', 'phone', 'tracking_id']
    date_hierarchy = 'created_at'
    list_per_page = 20

    def user_link(self, obj):
        link = reverse("admin:users_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', link, obj.user.username)
    user_link.short_description = 'User'

    def total_display(self, obj):
        return f"{obj.total} BDT"
    total_display.short_description = 'Total Amount'

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Items'

    def products_list(self, obj):
        return ", ".join([str(item.product.title) for item in obj.items.all()])
    products_list.short_description = 'Products'

    inlines = [OrderItemInline]
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered']
    readonly_fields = ['created_at', 'updated_at']

    def invoice_actions(self, obj):
        url = reverse('order_invoice', args=[obj.id])
        return format_html('<a class="button" href="{}" target="_blank">PDF Invoice</a>', url)
    invoice_actions.short_description = 'Invoice'

    def mark_as_processing(self, request, queryset):
        queryset.update(status='processing')
    mark_as_processing.short_description = "Mark selected orders as Processing"

    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')
    mark_as_shipped.short_description = "Mark selected orders as Shipped"

    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')
    mark_as_delivered.short_description = "Mark selected orders as Delivered"
