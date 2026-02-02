from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Product, StockAlert
from django.core.mail import send_mail
from django.conf import settings

@receiver(post_save, sender=Product)
def notify_back_in_stock(sender, instance, created, **kwargs):
    """
    Signal to notify users when a product becomes in stock.
    """
    if not created:
        # Check if stock changed from 0 to >0
        # For simplicity, we trigger if in_stock is True and there are pending alerts
        if instance.in_stock and instance.stock_quantity > 0:
            alerts = StockAlert.objects.filter(product=instance, is_notified=False)
            
            for alert in alerts:
                subject = f"Good News! {instance.title} is back in stock"
                message = f"Hi {alert.user.username if alert.user else 'there'},\n\nThe product '{instance.title}' you were waiting for is back in stock. Grab it before it's gone!\n\nShop now: {settings.SITE_URL if hasattr(settings, 'SITE_URL') else ''}{instance.get_absolute_url()}\n\nBest regards,\nAl Barakah Mart"
                
                recipient = alert.email or (alert.user.email if alert.user else None)
                
                if recipient:
                    try:
                        # In a real environment, use a task queue like Celery
                        # For now, we print to console/log
                        print(f"Sending back-in-stock email to {recipient} for {instance.title}")
                        # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient])
                        alert.is_notified = True
                        alert.save()
                    except Exception as e:
                        print(f"Failed to send stock alert email: {e}")
