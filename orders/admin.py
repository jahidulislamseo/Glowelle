from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Order, OrderItem, Courier, PaymentGateway, OrderStatusHistory
from import_export.admin import ImportExportModelAdmin

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price']

@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'created_by', 'created_at']
    readonly_fields = ['created_at']

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['created_by', 'created_at']
    can_delete = False

    def has_add_permission(self, request, obj):
        return False

@admin.register(Order)
class OrderAdmin(ImportExportModelAdmin):
    change_form_template = 'admin/orders/order/change_form.html'
    
    list_display = [
        'order_reference', 'id', 'user_link', 'status', 'total_display', 
        'payment_status', 'items_count', 'created_at', 'invoice_actions'
    ]
    list_editable = ['status']
    list_filter = [
        'status', 'payment_status', 'payment_method', 'created_at', 
        'courier', 'is_high_risk', 'source'
    ]
    search_fields = [
        'id', 'order_reference', 'user__username', 'user__email', 
        'phone', 'tracking_id', 'invoice_number', 'transaction_id'
    ]
    date_hierarchy = 'created_at'
    list_per_page = 20
    
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    # Organize fields for the "Standard" view (fallback or add form)
    fieldsets = (
        ('Identity', {
            'fields': ('order_reference', 'source', 'user', 'status', 'is_archived')
        }),
        ('Customer', {
            'fields': ('full_name', 'email', 'phone', 'address', 'city', 'zip_code', 'ip_address')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_status', 'total', 'subtotal', 'tax_amount', 'delivery_charge', 'discount_amount')
        }),
        ('Delivery', {
            'fields': ('courier', 'tracking_id', 'shipping_label', 'estimated_delivery_date', 'actual_delivery_date')
        }),
        ('Admin', {
            'fields': ('internal_admin_note', 'is_high_risk', 'risk_score')
        }),
    )

    def user_link(self, obj):
        link = reverse("admin:users_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', link, obj.user.username)
    user_link.short_description = 'User'

    def total_display(self, obj):
        return f"{obj.total} BDT"
    total_display.short_description = 'Total'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'shipped': 'purple',
            'delivered': 'green',
            'cancelled': 'red',
            'returned': 'gray',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Items'

    def products_list(self, obj):
        return ", ".join([str(item.product.title) for item in obj.items.all()])
    products_list.short_description = 'Products'

    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_paid']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['created_at', 'updated_at', 'order_reference', 'subtotal', 'total', 'ip_address']
        return []

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def invoice_actions(self, obj):
        # Placeholder for invoice URL
        return format_html('<a class="button" href="#" target="_blank">PDF Invoice</a>')
    invoice_actions.short_description = 'Invoice'

    def mark_as_processing(self, request, queryset):
        queryset.update(status='processing')
    mark_as_processing.short_description = "Mark selected orders as Processing"

    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')
    mark_as_shipped.short_description = "Mark selected orders as Shipped"

    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered', actual_delivery_date=timezone.now())
    mark_as_delivered.short_description = "Mark selected orders as Delivered"
    
    def mark_as_paid(self, request, queryset):
        queryset.update(payment_status='paid', payment_date=timezone.now())
    mark_as_paid.short_description = "Mark selected orders as Paid"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        try:
            order = Order.objects.get(pk=object_id)
            extra_context['timeline'] = order.status_history.all()
            
            # Customer Lifetime Stats
            user_orders = Order.objects.filter(user=order.user)
            extra_context['customer_total_orders'] = user_orders.count()
            extra_context['customer_lifetime_spend'] = sum(o.total for o in user_orders)
            extra_context['customer_first_order'] = user_orders.order_by('created_at').first().created_at
            
        except Order.DoesNotExist:
            pass
            
        return super().change_view(request, object_id, form_url, extra_context=extra_context)
