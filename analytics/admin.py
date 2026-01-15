from django.contrib import admin
from .models import VisitorSession, PageView, AnalyticsEvent

@admin.register(VisitorSession)
class VisitorSessionAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'user', 'ip_address', 'device_type', 'start_time', 'is_bounce')
    list_filter = ('device_type', 'is_bounce', 'start_time')
    search_fields = ('session_key', 'user__username', 'ip_address')
    readonly_fields = ('start_time', 'last_seen')

@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'url', 'method', 'status_code', 'response_time_ms', 'session_link')
    list_filter = ('method', 'status_code', 'timestamp')
    search_fields = ('url',)
    
    def session_link(self, obj):
        return obj.session.session_key
    session_link.short_description = 'Session'

@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'event_type', 'value', 'user', 'session_link')
    list_filter = ('event_type', 'timestamp')
    search_fields = ('value', 'user__username', 'user__email')
    
    def session_link(self, obj):
        return obj.session.session_key
    session_link.short_description = 'Session'
