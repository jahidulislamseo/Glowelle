from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from .models import AnalyticsEvent, VisitorSession
from django.db.models.signals import post_save
from django.conf import settings

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    # Link session to user
    if request:
        session_key = request.session.session_key
        VisitorSession.objects.filter(session_key=session_key).update(user=user)
        
        # Log Event
        session = VisitorSession.objects.filter(session_key=session_key).first()
        if session:
            AnalyticsEvent.objects.create(
                session=session,
                user=user,
                event_type='login'
            )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if request:
        session = VisitorSession.objects.filter(session_key=request.session.session_key).first()
        if session:
            AnalyticsEvent.objects.create(
                session=session,
                user=user,
                event_type='logout'
            )

# Note: Signup is usually handled by Views or Allauth signals, assuming standard view handling for now.
