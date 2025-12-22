from django.contrib import admin
from .models import SiteSettings

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['site_title', 'ga4_tracking_id']
    
    def has_add_permission(self, request):
        # Only allow 1 instance
        if SiteSettings.objects.exists():
            return False
        return True


