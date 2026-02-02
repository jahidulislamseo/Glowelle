from django.contrib import admin
from .models import ChatbotFAQ, ChatbotSettings, ChatbotSuggestion, ChatbotIntent

@admin.register(ChatbotFAQ)
class ChatbotFAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'keywords', 'is_active', 'updated_at']
    list_filter = ['is_active']
    search_fields = ['question', 'keywords', 'answer']
    list_editable = ['is_active']

@admin.register(ChatbotSettings)
class ChatbotSettingsAdmin(admin.ModelAdmin):
    list_display = ['__str__']
    
    fieldsets = (
        ('Greetings & Logic', {
            'fields': ('welcome_message', 'system_prompt', 'not_found_message')
        }),
        ('Support & Working Hours', {
            'fields': (('working_hours_start', 'working_hours_end'), 'offline_message')
        }),
        ('Promotions', {
            'fields': ('is_promo_active', 'promo_message')
        }),
    )
    
    def has_add_permission(self, request):
        if ChatbotSettings.objects.exists():
            return False
        return True

@admin.register(ChatbotSuggestion)
class ChatbotSuggestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'action', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    ordering = ['order']

@admin.register(ChatbotIntent)
class ChatbotIntentAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'intent_key']
    search_fields = ['display_name', 'keywords']
