from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Product, StockAlert
from core.email_utils import send_stock_alert_email, send_admin_low_stock_email

LOW_STOCK_THRESHOLD = 10

_product_prev_stock = {}


@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def clear_product_cache(sender, instance, **kwargs):
    cache.delete('home_page_data')


@receiver(pre_save, sender=Product)
def capture_old_stock(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Product.objects.get(pk=instance.pk)
            _product_prev_stock[instance.pk] = old.stock_quantity
        except Product.DoesNotExist:
            pass


@receiver(post_save, sender=Product)
def notify_back_in_stock(sender, instance, created, **kwargs):
    if created:
        _product_prev_stock.pop(instance.pk, None)
        return

    old_stock = _product_prev_stock.pop(instance.pk, None)

    # Back-in-stock: notify waiting customers
    if instance.in_stock and instance.stock_quantity > 0:
        alerts = StockAlert.objects.filter(product=instance, is_notified=False)
        for alert in alerts:
            recipient = alert.email or (alert.user.email if alert.user else None)
            username = alert.user.username if alert.user else 'Customer'
            if recipient:
                try:
                    send_stock_alert_email(recipient, username, instance)
                    alert.is_notified = True
                    alert.save()
                except Exception as e:
                    print(f"Failed to send stock alert email: {e}")

    # Low-stock: alert admin when stock drops below threshold for the first time
    if (
        old_stock is not None
        and old_stock >= LOW_STOCK_THRESHOLD
        and instance.stock_quantity < LOW_STOCK_THRESHOLD
        and instance.in_stock
    ):
        try:
            send_admin_low_stock_email([instance])
        except Exception as e:
            print(f"Failed to send low stock admin email: {e}")
