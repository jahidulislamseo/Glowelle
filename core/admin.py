from django.contrib import admin
from django import forms
from .models import SiteSettings, ContactMessage

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
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
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'created_at', 'is_read']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'message']
    list_editable = ['is_read']
    readonly_fields = ['created_at']
