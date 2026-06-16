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
from core.admin_mixins import ChangeHistoryMixin


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
class ChatbotSettingsAdmin(ChangeHistoryMixin, admin.ModelAdmin):
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
class ChatbotFAQAdmin(ChangeHistoryMixin, admin.ModelAdmin):
    list_display = ('question', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('question', 'answer', 'keywords')
    list_editable = ('is_active',)


@admin.register(ChatbotSuggestion)
class ChatbotSuggestionAdmin(ChangeHistoryMixin, admin.ModelAdmin):
    list_display = ('text', 'action', 'order', 'is_active')
    list_filter = ('is_active', 'action')
    list_editable = ('order', 'is_active')
    ordering = ('order',)


@admin.register(ChatbotIntent)
class ChatbotIntentAdmin(ChangeHistoryMixin, admin.ModelAdmin):
    list_display = ('intent_key', 'display_name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('intent_key', 'display_name', 'keywords')
    list_editable = ('is_active',)


@admin.register(ChatbotConversationMemory)
class ChatbotConversationMemoryAdmin(admin.ModelAdmin):
    list_display = ('session_id_short', 'user_message_full', 'bot_response_full', 'intent_badge', 'greeting_count', 'created_at')
    list_display_links = ('session_id_short',)
    list_filter = ('detected_intent', ('created_at', admin.DateFieldListFilter))
    search_fields = ('session_id', 'user_message', 'bot_response', 'detected_intent')
    readonly_fields = ('session_id', 'user_message', 'bot_response', 'detected_intent',
                      'user_preferences_display', 'greeting_count', 'created_at')
    date_hierarchy = 'created_at'
    list_per_page = 25
    ordering = ('-created_at',)
    actions = ['delete_selected_memories']

    INTENT_COLORS = {
        'greeting': '#28a745',
        'product_query': '#007bff',
        'order': '#fd7e14',
        'support': '#dc3545',
        'discount': '#6f42c1',
        'faq': '#17a2b8',
    }

    def session_id_short(self, obj):
        short = obj.session_id[:10] + '…' if len(obj.session_id) > 10 else obj.session_id
        return format_html('<code style="font-size:11px;color:#555;">{}</code>', short)
    session_id_short.short_description = 'Session'

    def user_message_full(self, obj):
        return format_html(
            '<div style="max-width:280px;max-height:80px;overflow-y:auto;'
            'white-space:pre-wrap;word-break:break-word;font-size:12px;'
            'background:#f8f9fa;padding:4px 6px;border-radius:4px;'
            'border-left:3px solid #007bff;">{}</div>',
            obj.user_message
        )
    user_message_full.short_description = 'User Message'

    def bot_response_full(self, obj):
        return format_html(
            '<div style="max-width:300px;max-height:80px;overflow-y:auto;'
            'white-space:pre-wrap;word-break:break-word;font-size:12px;'
            'background:#f0fff4;padding:4px 6px;border-radius:4px;'
            'border-left:3px solid #28a745;color:#333;">{}</div>',
            obj.bot_response
        )
    bot_response_full.short_description = 'Bot Response'

    def intent_badge(self, obj):
        intent = obj.detected_intent or 'unknown'
        color = self.INTENT_COLORS.get(intent, '#6c757d')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;">{}</span>',
            color, intent
        )
    intent_badge.short_description = 'Intent'

    def user_preferences_display(self, obj):
        if not obj.user_preferences:
            return '—'
        rows = ''.join(
            f'<tr><td style="padding:3px 8px;font-weight:600;">{k}</td>'
            f'<td style="padding:3px 8px;">{v}</td></tr>'
            for k, v in obj.user_preferences.items()
        )
        return format_html(
            '<table style="border-collapse:collapse;font-size:13px;">'
            '<thead><tr><th style="padding:3px 8px;border-bottom:1px solid #ddd;">Key</th>'
            '<th style="padding:3px 8px;border-bottom:1px solid #ddd;">Value</th></tr></thead>'
            '<tbody>{}</tbody></table>',
            format_html(rows)
        )
    user_preferences_display.short_description = 'User Preferences'

    def get_fieldsets(self, request, obj=None):
        return (
            ('Session Info', {
                'fields': ('session_id', 'detected_intent', 'greeting_count', 'created_at'),
            }),
            ('Conversation', {
                'fields': ('user_message', 'bot_response'),
            }),
            ('Preferences', {
                'fields': ('user_preferences_display',),
                'classes': ('collapse',),
            }),
        )

    def delete_selected_memories(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} conversation memory record(s) deleted.')
    delete_selected_memories.short_description = 'Delete selected memories'

    def has_add_permission(self, request):
        return False
