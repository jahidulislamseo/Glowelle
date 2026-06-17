from django.contrib import admin
from django import forms
from .models import SiteSettings, ContactMessage, ErrorLog
from core.admin_mixins import ChangeHistoryMixin

@admin.register(SiteSettings)
class SiteSettingsAdmin(ChangeHistoryMixin, admin.ModelAdmin):
    list_display = ['site_title', 'support_email']
    
    fieldsets = (
        ('General', {
            'fields': ('site_title', 'meta_description')
        }),
        ('Branding', {
            'fields': ('logo', 'favicon')
        }),
        ('Contact Info', {
            'fields': ('support_email', 'support_phone', 'address')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'instagram_url', 'twitter_url', 'youtube_url'),
            'classes': ('collapse',)
        }),
        ('Analytics (Technical)', {
            'fields': ('ga4_tracking_id', 'search_console_code'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # Only allow 1 instance
        if SiteSettings.objects.exists():
            return False
        return True

@admin.register(ContactMessage)
class ContactMessageAdmin(ChangeHistoryMixin, admin.ModelAdmin):
    list_display = ['name', 'email', 'created_at', 'is_read']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'message']
    list_editable = ['is_read']
    readonly_fields = ['created_at']


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ['level', 'short_message', 'path', 'user', 'is_resolved', 'created_at']
    list_filter = ['level', 'is_resolved', 'created_at']
    search_fields = ['message', 'path', 'user']
    list_editable = ['is_resolved']
    readonly_fields = ['level', 'message', 'traceback', 'path', 'method', 'user', 'ip_address', 'created_at']
    ordering = ['-created_at']

    def short_message(self, obj):
        return obj.message[:80]
    short_message.short_description = 'Message'

    def has_add_permission(self, request):
        return False
