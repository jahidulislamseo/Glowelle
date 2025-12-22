from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import Order

@receiver(post_save, sender=Order)
def send_order_notification(sender, instance, created, **kwargs):
    user = instance.user
    subject = ""
    template = ""
    
    if created:
        subject = f"Order Confirmation - #{instance.id}"
        template = "emails/order_confirmation.html"
    else:
        # Check if status changed? (Requires tracking old status, simplistic approach for now)
        # For simplicity in this MV, we only verify Confirmation on Create.
        # Handling status updates properly requires a pre_save signal or field tracker.
        return 

    if template:
        html_message = render_to_string(template, {'order': instance, 'user': user, 'site_url': 'http://127.0.0.1:8000'}) # site_url hardcoded for dev
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False, # We want to see errors in dev
            )
            print(f"Email sent to {user.email} for Order #{instance.id}")
        except Exception as e:
            print(f"Failed to send email: {e}")
