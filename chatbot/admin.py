from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta
from .analytics_models import ChatbotAnalytics, ChatbotMetric, PopularProduct
from .models import (
    ChatbotSettings, ChatbotFAQ, ChatbotSuggestion, 
    ChatbotIntent, ChatbotConversationMemory
)


@admin.register(ChatbotAnalytics)
class ChatbotAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_conversations', 'total_orders', 'conversion_rate_display', 'unique_users')
    list_filter = ('date',)
    readonly_fields = ('date', 'total_conversations', 'total_messages', 'total_orders', 
                      'conversion_rate', 'average_messages_per_session', 'unique_users')
    
    def conversion_rate_display(self, obj):
        return format_html('<b style="color: green;">{:.2f}%</b>', obj.conversion_rate)
    conversion_rate_display.short_description = 'Conversion Rate'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        # Add summary statistics
        extra_context = extra_context or {}
        
        # Last 7 days stats
        seven_days_ago = timezone.now().date() - timedelta(days=7)
        recent_analytics = ChatbotAnalytics.objects.filter(date__gte=seven_days_ago)
        
        extra_context['total_conversations_7d'] = sum(a.total_conversations for a in recent_analytics)
        extra_context['total_orders_7d'] = sum(a.total_orders for a in recent_analytics)
        extra_context['avg_conversion_7d'] = recent_analytics.aggregate(Avg('conversion_rate'))['conversion_rate__avg'] or 0
        
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(ChatbotMetric)
class ChatbotMetricAdmin(admin.ModelAdmin):
    list_display = ('session_id_short', 'user', 'started_at', 'messages_count', 
                   'resulted_in_order', 'order_link', 'user_rating_display')
    list_filter = ('resulted_in_order', 'started_at', 'user_rating')
    search_fields = ('session_id', 'user__username', 'user__email')
    readonly_fields = ('session_id', 'user', 'started_at', 'ended_at', 'messages_count', 
                      'resulted_in_order', 'order', 'detected_intents')
    
    def session_id_short(self, obj):
        return obj.session_id[:12] + '...' if len(obj.session_id) > 12 else obj.session_id
    session_id_short.short_description = 'Session ID'
    
    def order_link(self, obj):
        if obj.order:
            return format_html('<a href="/admin/orders/order/{}/change/">{}</a>', 
                             obj.order.id, obj.order.order_reference)
        return '-'
    order_link.short_description = 'Order'
    
    def user_rating_display(self, obj):
        if obj.user_rating:
            stars = '⭐' * obj.user_rating
            return format_html('<span title="{}/5">{}</span>', obj.user_rating, stars)
        return '-'
    user_rating_display.short_description = 'Rating'
    
    def has_add_permission(self, request):
        return False


@admin.register(PopularProduct)
class PopularProductAdmin(admin.ModelAdmin):
    list_display = ('product', 'date', 'query_count', 'order_count', 'conversion_rate_display')
    list_filter = ('date',)
    search_fields = ('product__title',)
    readonly_fields = ('product', 'date', 'query_count', 'order_count')
    
    def conversion_rate_display(self, obj):
        if obj.query_count > 0:
            rate = (obj.order_count / obj.query_count) * 100
            return format_html('<b>{:.1f}%</b>', rate)
        return '0%'
    conversion_rate_display.short_description = 'Conversion'
    
    def has_add_permission(self, request):
        return False


@admin.register(ChatbotSettings)
class ChatbotSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'welcome_message_short', 'is_promo_active')
    fieldsets = (
        ('Basic Settings', {
            'fields': ('welcome_message', 'system_prompt')
        }),
        ('Promo Settings', {
            'fields': ('is_promo_active', 'promo_message')
        }),
    )
    
    def welcome_message_short(self, obj):
        return obj.welcome_message[:50] + '...' if len(obj.welcome_message) > 50 else obj.welcome_message
    welcome_message_short.short_description = 'Welcome Message'


@admin.register(ChatbotFAQ)
class ChatbotFAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('question', 'answer', 'keywords')
    list_editable = ('is_active',)


@admin.register(ChatbotSuggestion)
class ChatbotSuggestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'action', 'order', 'is_active')
    list_filter = ('is_active', 'action')
    list_editable = ('order', 'is_active')
    ordering = ('order',)


@admin.register(ChatbotIntent)
class ChatbotIntentAdmin(admin.ModelAdmin):
    list_display = ('intent_key', 'display_name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('intent_key', 'display_name', 'keywords')
    list_editable = ('is_active',)


@admin.register(ChatbotConversationMemory)
class ChatbotConversationMemoryAdmin(admin.ModelAdmin):
    list_display = ('session_id_short', 'user_message_short', 'detected_intent', 'greeting_count', 'created_at')
    list_filter = ('detected_intent', 'created_at')
    search_fields = ('session_id', 'user_message', 'bot_response')
    readonly_fields = ('session_id', 'user_message', 'bot_response', 'detected_intent', 
                      'user_preferences', 'greeting_count', 'created_at')
    
    def session_id_short(self, obj):
        return obj.session_id[:12] + '...' if len(obj.session_id) > 12 else obj.session_id
    session_id_short.short_description = 'Session'
    
    def user_message_short(self, obj):
        return obj.user_message[:50] + '...' if len(obj.user_message) > 50 else obj.user_message
    user_message_short.short_description = 'Message'
    
    def has_add_permission(self, request):
        return False
