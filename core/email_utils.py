from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

SITE_URL = getattr(settings, 'SITE_URL', 'http://localhost:8000')
LOGO_URL = f"{SITE_URL}/static/images/logo.png"
SUPPORT_PHONE = "+8801600818139"
SUPPORT_EMAIL = "info@nyveralife.com"
SUPPORT_EMAIL_2 = "support@nyveralife.com"


def send_template_email(subject, template, context, recipient_list, from_email=None):
    context.setdefault('site_url', SITE_URL)
    context.setdefault('logo_url', LOGO_URL)
    context.setdefault('support_phone', SUPPORT_PHONE)
    context.setdefault('support_email', SUPPORT_EMAIL)
    context.setdefault('support_email_2', SUPPORT_EMAIL_2)

    if isinstance(recipient_list, str):
        recipient_list = [recipient_list]

    html_message = render_to_string(template, context)
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"[Email Error] {subject} → {recipient_list}: {e}")
        return False


def send_welcome_email(user):
    send_template_email(
        subject="Nyveralife-তে স্বাগতম! 🎉",
        template="emails/welcome.html",
        context={'user': user},
        recipient_list=user.email,
    )


def send_order_confirmation_email(order):
    recipient = order.user.email if order.user else order.email
    customer_name = (order.user.first_name or order.user.username) if order.user else order.full_name
    send_template_email(
        subject=f"অর্ডার কনফার্মেশন - #{order.order_reference or order.id}",
        template="emails/order_confirmation.html",
        context={'order': order, 'customer_name': customer_name},
        recipient_list=recipient,
    )


def send_order_status_email(order):
    recipient = order.user.email if order.user else order.email
    customer_name = (order.user.first_name or order.user.username) if order.user else order.full_name
    send_template_email(
        subject=f"অর্ডার আপডেট - #{order.order_reference or order.id}",
        template="emails/order_status_update.html",
        context={'order': order, 'customer_name': customer_name},
        recipient_list=recipient,
    )


def send_otp_email(user, otp_code):
    send_template_email(
        subject="আপনার Nyveralife OTP কোড",
        template="emails/otp_verification.html",
        context={'user': user, 'otp_code': otp_code},
        recipient_list=user.email,
    )


def send_stock_alert_email(user_email, username, product):
    send_template_email(
        subject=f"সুখবর! '{product.title}' এখন স্টকে আছে",
        template="emails/stock_alert.html",
        context={'username': username, 'product': product},
        recipient_list=user_email,
    )


def send_wallet_credit_email(user, amount, description, new_balance):
    send_template_email(
        subject=f"৳{amount} Wallet-এ যোগ হয়েছে",
        template="emails/wallet_credit.html",
        context={'user': user, 'amount': amount, 'description': description, 'new_balance': new_balance},
        recipient_list=user.email,
    )


def send_support_ticket_email(ticket):
    send_template_email(
        subject=f"Support Ticket #{ticket.id} পাওয়া গেছে",
        template="emails/support_ticket_created.html",
        context={'ticket': ticket},
        recipient_list=ticket.user.email,
    )


def send_return_refund_email(order):
    recipient = order.user.email if order.user else order.email
    customer_name = (order.user.first_name or order.user.username) if order.user else order.full_name
    send_template_email(
        subject=f"Return/Refund আপডেট - #{order.order_reference or order.id}",
        template="emails/return_refund_update.html",
        context={'order': order, 'customer_name': customer_name},
        recipient_list=recipient,
    )


# --- Admin Notification Emails ---

def send_admin_new_order_email(order):
    admin_email = getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)
    send_template_email(
        subject=f"[New Order] #{order.order_reference or order.id} - ৳{order.total}",
        template="emails/admin_new_order.html",
        context={'order': order},
        recipient_list=admin_email,
    )


def send_admin_contact_email(contact_message):
    admin_email = getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)
    send_template_email(
        subject=f"[Contact Form] New message from {contact_message.name}",
        template="emails/admin_contact_message.html",
        context={'msg': contact_message},
        recipient_list=admin_email,
    )


def send_admin_new_ticket_email(ticket):
    admin_email = getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)
    send_template_email(
        subject=f"[New Ticket #{ticket.id}] {ticket.subject}",
        template="emails/admin_new_ticket.html",
        context={'ticket': ticket},
        recipient_list=admin_email,
    )


def send_admin_low_stock_email(products):
    admin_email = getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)
    send_template_email(
        subject=f"[Low Stock Alert] {len(products)} products are running low",
        template="emails/admin_low_stock.html",
        context={'products': products},
        recipient_list=admin_email,
    )
