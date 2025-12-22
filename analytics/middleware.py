import time
from .models import VisitorSession, PageView, AnalyticsEvent
from django.utils import timezone
from django.conf import settings

class AnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Skip static/media/admin requests to reduce noise
        if request.path.startswith(settings.STATIC_URL) or \
           request.path.startswith(settings.MEDIA_URL) or \
           request.path.startswith('/admin/') or \
           'favicon.ico' in request.path:
            return self.get_response(request)

        start_time = time.time()

        # 2. Get or Create Visitor Session
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        visitor_session, created = VisitorSession.objects.get_or_create(
            session_key=session_key
        )
        
        # Update User if logged in
        if request.user.is_authenticated and not visitor_session.user:
            visitor_session.user = request.user
            visitor_session.save()
            
        # Update IP/Device info only on creation (to save write ops) or occasionally
        if created:
            visitor_session.ip_address = self.get_client_ip(request)
            visitor_session.user_agent = request.META.get('HTTP_USER_AGENT', '')
            # Simple device detection could be improved with libraries
            ua = visitor_session.user_agent.lower()
            if 'mobile' in ua:
                visitor_session.device_type = 'mobile'
            elif 'tablet' in ua:
                visitor_session.device_type = 'tablet'
            visitor_session.save()

        # 3. Process Request
        response = self.get_response(request)

        # 4. Log Page View
        duration = int((time.time() - start_time) * 1000) # ms
        
        # Check if 404
        if response.status_code == 404:
            AnalyticsEvent.objects.create(
                session=visitor_session,
                user=request.user if request.user.is_authenticated else None,
                event_type='error_404',
                value=request.path,
                url=request.build_absolute_uri()
            )
        
        # Create PageView
        PageView.objects.create(
            session=visitor_session,
            url=request.path[:1000],
            referer=request.META.get('HTTP_REFERER', '')[:1000],
            status_code=response.status_code,
            method=request.method,
            response_time_ms=duration
        )
        
        # Update Last Seen & Unbounce
        visitor_session.last_seen = timezone.now()
        # If user has > 1 page view, it's not a bounce
        if created:
             visitor_session.is_bounce = True # Starts as bounce
        elif visitor_session.is_bounce:
             # If this is a subsequent request, it's no longer a bounce
             count = visitor_session.page_views.count()
             if count > 1:
                 visitor_session.is_bounce = False
                 
        visitor_session.save()

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
