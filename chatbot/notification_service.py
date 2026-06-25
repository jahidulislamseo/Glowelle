"""
Notification Service for Nyveralife
Handles SMS, Email, and WhatsApp notifications for order updates.
"""

import os
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from twilio.rest import Client
from decouple import config


class NotificationService:
    """
    Unified notification service for all channels.
    """
    
    def __init__(self):
        # Twilio setup for SMS and WhatsApp
        self.twilio_account_sid = config('TWILIO_ACCOUNT_SID', default=None)
        self.twilio_auth_token = config('TWILIO_AUTH_TOKEN', default=None)
        self.twilio_phone = config('TWILIO_PHONE_NUMBER', default=None)
        self.twilio_whatsapp = config('TWILIO_WHATSAPP_NUMBER', default=None)
        
        if self.twilio_account_sid and self.twilio_auth_token:
            self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
        else:
            self.twilio_client = None
    
    def send_order_notification(self, order, status_change=None):
        """
        Send notification for order update across all enabled channels.
        """
        results = {
            'sms': False,
            'email': False,
            'whatsapp': False
        }
        
        # Prepare message content
        message = self._get_order_message(order, status_change)
        
        # Send SMS
        if self.twilio_client and order.phone:
            results['sms'] = self._send_sms(order.phone, message)
        
        # Send Email
        if order.user and order.user.email:
            from core.email_utils import send_order_status_email
            results['email'] = send_order_status_email(order)
        
        # Send WhatsApp
        if self.twilio_client and order.phone:
            results['whatsapp'] = self._send_whatsapp(order.phone, message)
        
        return results
    
    def _get_order_message(self, order, status_change=None):
        """
        Generate order notification message in Bangla.
        """
        status_messages = {
            'pending': '⏳ আপনার অর্ডার গ্রহণ করা হয়েছে',
            'processing': '🔄 আপনার অর্ডার প্রস্তুত করা হচ্ছে',
            'shipped': '🚚 আপনার অর্ডার পাঠানো হয়েছে',
            'delivered': '✅ আপনার অর্ডার ডেলিভার হয়েছে',
            'cancelled': '❌ আপনার অর্ডার বাতিল করা হয়েছে'
        }
        
        status_text = status_messages.get(order.status, order.get_status_display())
        
        message = f"""🛒 Nyveralife

{status_text}

📦 Order: {order.order_reference}
💰 Total: {order.total} BDT
📅 Date: {order.created_at.strftime('%d %b, %Y')}

"""
        
        if order.status == 'shipped':
            message += "🚚 আপনার অর্ডার ১-২ দিনের মধ্যে পৌঁছাবে।\n"
        elif order.status == 'delivered':
            message += "🎉 আমাদের সাথে কেনাকাটা করার জন্য ধন্যবাদ!\n"
        elif order.status == 'pending':
            message += "📞 শীঘ্রই আমরা আপনার সাথে যোগাযোগ করব।\n"
        
        message += f"\n📞 Support: {config('SUPPORT_PHONE', default='+8801600818139')}"
        
        return message
    
    def _format_phone(self, phone):
        """
        Format phone number for Bangladesh with correct country prefix.
        """
        phone = phone.strip()
        if not phone.startswith('+'):
            if phone.startswith('88'):
                phone = '+' + phone
            elif phone.startswith('0'):
                phone = '+88' + phone[1:]
            else:
                phone = '+88' + phone
        return phone

    def _send_sms(self, phone, message):
        """
        Send SMS notification via Twilio.
        """
        if not self.twilio_client or not self.twilio_phone:
            return False
        
        try:
            phone = self._format_phone(phone)
            
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone,
                to=phone
            )
            
            return message_obj.sid is not None
        except Exception as e:
            print(f"SMS Error: {e}")
            return False
    
    def _send_email(self, email, order, status_change=None):
        """
        Send email notification.
        """
        try:
            status_subjects = {
                'pending': 'Order Confirmation',
                'processing': 'Order Processing',
                'shipped': 'Order Shipped',
                'delivered': 'Order Delivered',
                'cancelled': 'Order Cancelled'
            }
            
            subject = f"Nyveralife - {status_subjects.get(order.status, 'Order Update')} #{order.order_reference}"
            
            # Create HTML email
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #28a745; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background: #f9f9f9; }}
                    .order-details {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                    .footer {{ text-align: center; padding: 20px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🛒 Nyveralife</h1>
                    </div>
                    <div class="content">
                        <h2>{self._get_order_message(order, status_change).split('\\n')[1]}</h2>
                        <div class="order-details">
                            <p><strong>Order Reference:</strong> {order.order_reference}</p>
                            <p><strong>Order Date:</strong> {order.created_at.strftime('%d %B, %Y')}</p>
                            <p><strong>Total Amount:</strong> {order.total} BDT</p>
                            <p><strong>Status:</strong> {order.get_status_display()}</p>
                            <p><strong>Delivery Address:</strong><br>{order.address}, {order.city}</p>
                        </div>
                        <h3>Order Items:</h3>
                        <ul>
            """
            
            for item in order.items.all():
                html_message += f"<li>{item.product.title} - {item.quantity} x {item.price} BDT = {item.quantity * item.price} BDT</li>"
            
            html_message += f"""
                        </ul>
                    </div>
                    <div class="footer">
                        <p>Thank you for shopping with Nyveralife!</p>
                        <p>📞 Support: {config('SUPPORT_PHONE', default='+8801600818139')}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            send_mail(
                subject=subject,
                message=self._get_order_message(order, status_change),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return True
        except Exception as e:
            print(f"Email Error: {e}")
            return False
    
    def _send_whatsapp(self, phone, message):
        """
        Send WhatsApp notification via Twilio.
        """
        if not self.twilio_client or not self.twilio_whatsapp:
            return False
        
        try:
            phone = self._format_phone(phone)
            
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=f'whatsapp:{self.twilio_whatsapp}',
                to=f'whatsapp:{phone}'
            )
            
            return message_obj.sid is not None
        except Exception as e:
            print(f"WhatsApp Error: {e}")
            return False


# Singleton instance
_notification_service = None

def get_notification_service():
    """
    Get or create notification service instance.
    """
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service


def send_order_notification(order, status_change=None):
    """
    Helper function to send order notification.
    """
    service = get_notification_service()
    return service.send_order_notification(order, status_change)
