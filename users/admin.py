from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count
from .models import User, Address, Wallet, SupportTicket

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'get_order_count', 'get_total_spent', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'image')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    def get_order_count(self, obj):
        return obj.orders.count()
    get_order_count.short_description = 'Orders'
    get_order_count.admin_order_field = 'orders_count'

    def get_total_spent(self, obj):
        total = obj.orders.filter(status='completed').aggregate(Sum('total'))['total__sum']
        return f"৳ {total or 0}"
    get_total_spent.short_description = 'Total Spent'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(orders_count=Count('orders'))
        return queryset

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'street', 'city', 'phone', 'is_default')
    list_filter = ('city', 'is_default')
    search_fields = ('user__email', 'street', 'phone')

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'user', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('subject', 'message', 'user__email')
    list_editable = ('status',)

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'currency')
    search_fields = ('user__email',)
