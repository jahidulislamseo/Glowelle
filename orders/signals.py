from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Order
from core.email_utils import (
    send_order_confirmation_email,
    send_order_status_email,
    send_admin_new_order_email,
    send_return_refund_email,
)

_order_prev_status = {}
_order_prev_return_status = {}


@receiver(pre_save, sender=Order)
def capture_old_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Order.objects.get(pk=instance.pk)
            _order_prev_status[instance.pk] = old.status
            _order_prev_return_status[instance.pk] = old.return_status
        except Order.DoesNotExist:
            pass


@receiver(post_save, sender=Order)
def send_order_notification(sender, instance, created, **kwargs):
    if created:
        send_order_confirmation_email(instance)
        send_admin_new_order_email(instance)
        _order_prev_status.pop(instance.pk, None)
        _order_prev_return_status.pop(instance.pk, None)
        return

    old_status = _order_prev_status.pop(instance.pk, None)
    old_return_status = _order_prev_return_status.pop(instance.pk, None)

    if old_status and old_status != instance.status:
        send_order_status_email(instance)

    if old_return_status and old_return_status != instance.return_status:
        if instance.return_status in ('approved', 'rejected', 'completed'):
            send_return_refund_email(instance)
