from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import WalletTransaction
from core.email_utils import send_wallet_credit_email


@receiver(post_save, sender=WalletTransaction)
def notify_wallet_credit(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.transaction_type != 'credit':
        return

    user = instance.wallet.user
    if not user.email:
        return

    try:
        send_wallet_credit_email(
            user=user,
            amount=instance.amount,
            description=instance.description,
            new_balance=instance.wallet.balance,
        )
    except Exception as e:
        print(f"Wallet credit email failed: {e}")
