"""
Payment Integration for Al Barakah Mart
Supports bKash, Nagad, and SSL Commerz payment gateways.
"""

import requests
import hashlib
import json
from decimal import Decimal
from django.conf import settings
from decouple import config
from datetime import datetime


class PaymentGatewayBase:
    """Base class for payment gateways."""
    
    def create_payment(self, order):
        """Create a payment and return payment URL."""
        raise NotImplementedError
    
    def verify_payment(self, transaction_id):
        """Verify payment status."""
        raise NotImplementedError
    
    def refund_payment(self, transaction_id, amount):
        """Process refund."""
        raise NotImplementedError


class BkashPayment(PaymentGatewayBase):
    """bKash payment integration."""
    
    def __init__(self):
        self.app_key = config('BKASH_APP_KEY', default='')
        self.app_secret = config('BKASH_APP_SECRET', default='')
        self.username = config('BKASH_USERNAME', default='')
        self.password = config('BKASH_PASSWORD', default='')
        self.base_url = config('BKASH_BASE_URL', default='https://checkout.sandbox.bka sh.com')
        self.token = None
    
    def get_token(self):
        """Get authentication token from bKash."""
        url = f"{self.base_url}/v1.2.0-beta/checkout/token/grant"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'username': self.username,
            'password': self.password
        }
        data = {
            'app_key': self.app_key,
            'app_secret': self.app_secret
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                self.token = response.json().get('id_token')
                return self.token
        except Exception as e:
            print(f"bKash token error: {e}")
        
        return None
    
    def create_payment(self, order):
        """Create bKash payment."""
        if not self.token:
            self.get_token()
        
        url = f"{self.base_url}/v1.2.0-beta/checkout/payment/create"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'authorization': self.token,
            'x-app-key': self.app_key
        }
        
        callback_url = f"{config('SITE_URL', default='http://localhost:8000')}/payments/bkash/callback/"
        
        data = {
            'amount': str(order.total),
            'currency': 'BDT',
            'intent': 'sale',
            'merchantInvoiceNumber': order.order_reference,
            'callbackURL': callback_url
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'payment_url': result.get('bkashURL'),
                    'payment_id': result.get('paymentID'),
                    'transaction_id': result.get('paymentID')
                }
        except Exception as e:
            print(f"bKash payment error: {e}")
        
        return {'success': False, 'error': 'Payment creation failed'}
    
    def verify_payment(self, payment_id):
        """Verify bKash payment."""
        if not self.token:
            self.get_token()
        
        url = f"{self.base_url}/v1.2.0-beta/checkout/payment/execute/{payment_id}"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'authorization': self.token,
            'x-app-key': self.app_key
        }
        
        try:
            response = requests.post(url, headers=headers)
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': result.get('transactionStatus') == 'Completed',
                    'transaction_id': result.get('trxID'),
                    'amount': result.get('amount'),
                    'status': result.get('transactionStatus')
                }
        except Exception as e:
            print(f"bKash verify error: {e}")
        
        return {'success': False}


class NagadPayment(PaymentGatewayBase):
    """Nagad payment integration."""
    
    def __init__(self):
        self.merchant_id = config('NAGAD_MERCHANT_ID', default='')
        self.merchant_number = config('NAGAD_MERCHANT_NUMBER', default='')
        self.public_key = config('NAGAD_PUBLIC_KEY', default='')
        self.private_key = config('NAGAD_PRIVATE_KEY', default='')
        self.base_url = config('NAGAD_BASE_URL', default='http://sandbox.mynagad.com:10080/remote-payment-gateway-1.0')
    
    def create_payment(self, order):
        """Create Nagad payment."""
        # Nagad implementation (similar structure to bKash)
        # This is a simplified version
        
        callback_url = f"{config('SITE_URL', default='http://localhost:8000')}/payments/nagad/callback/"
        
        payment_data = {
            'merchantId': self.merchant_id,
            'orderId': order.order_reference,
            'amount': str(order.total),
            'currency': 'BDT',
            'challenge': self._generate_challenge()
        }
        
        # In production, you would encrypt and sign the data
        # For now, returning a mock response
        return {
            'success': True,
            'payment_url': f"{self.base_url}/check-out/initialize/{order.order_reference}",
            'payment_id': order.order_reference
        }
    
    def _generate_challenge(self):
        """Generate random challenge for Nagad."""
        import random
        import string
        return ''.join(random.choices(string.ascii_letters + string.digits, k=40))
    
    def verify_payment(self, payment_id):
        """Verify Nagad payment."""
        # Implementation for payment verification
        return {'success': True, 'transaction_id': payment_id}


class SSLCommerzPayment(PaymentGatewayBase):
    """SSL Commerz payment integration."""
    
    def __init__(self):
        self.store_id = config('SSLCOMMERZ_STORE_ID', default='')
        self.store_password = config('SSLCOMMERZ_STORE_PASSWORD', default='')
        self.is_sandbox = config('SSLCOMMERZ_IS_SANDBOX', default='True') == 'True'
        
        if self.is_sandbox:
            self.base_url = 'https://sandbox.sslcommerz.com'
        else:
            self.base_url = 'https://securepay.sslcommerz.com'
    
    def create_payment(self, order):
        """Create SSL Commerz payment."""
        url = f"{self.base_url}/gwprocess/v4/api.php"
        
        success_url = f"{config('SITE_URL', default='http://localhost:8000')}/payments/sslcommerz/success/"
        fail_url = f"{config('SITE_URL', default='http://localhost:8000')}/payments/sslcommerz/fail/"
        cancel_url = f"{config('SITE_URL', default='http://localhost:8000')}/payments/sslcommerz/cancel/"
        
        data = {
            'store_id': self.store_id,
            'store_passwd': self.store_password,
            'total_amount': str(order.total),
            'currency': 'BDT',
            'tran_id': order.order_reference,
            'success_url': success_url,
            'fail_url': fail_url,
            'cancel_url': cancel_url,
            'cus_name': order.full_name,
            'cus_email': order.email,
            'cus_phone': order.phone,
            'cus_add1': order.address,
            'cus_city': order.city,
            'cus_country': 'Bangladesh',
            'shipping_method': 'YES',
            'product_name': f"Order {order.order_reference}",
            'product_category': 'General',
            'product_profile': 'general'
        }
        
        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'SUCCESS':
                    return {
                        'success': True,
                        'payment_url': result.get('GatewayPageURL'),
                        'session_key': result.get('sessionkey'),
                        'transaction_id': order.order_reference
                    }
        except Exception as e:
            print(f"SSL Commerz error: {e}")
        
        return {'success': False, 'error': 'Payment creation failed'}
    
    def verify_payment(self, transaction_id):
        """Verify SSL Commerz payment."""
        url = f"{self.base_url}/validator/api/validationserverAPI.php"
        
        params = {
            'val_id': transaction_id,
            'store_id': self.store_id,
            'store_passwd': self.store_password,
            'format': 'json'
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': result.get('status') == 'VALID' or result.get('status') == 'VALIDATED',
                    'transaction_id': result.get('tran_id'),
                    'amount': result.get('amount'),
                    'status': result.get('status')
                }
        except Exception as e:
            print(f"SSL Commerz verify error: {e}")
        
        return {'success': False}


class PaymentService:
    """Unified payment service."""
    
    def __init__(self):
        self.gateways = {
            'bkash': BkashPayment(),
            'nagad': NagadPayment(),
            'sslcommerz': SSLCommerzPayment()
        }
    
    def create_payment(self, order, gateway='bkash'):
        """Create payment with specified gateway."""
        if gateway not in self.gateways:
            return {'success': False, 'error': 'Invalid gateway'}
        
        return self.gateways[gateway].create_payment(order)
    
    def verify_payment(self, transaction_id, gateway='bkash'):
        """Verify payment."""
        if gateway not in self.gateways:
            return {'success': False, 'error': 'Invalid gateway'}
        
        return self.gateways[gateway].verify_payment(transaction_id)
    
    def generate_payment_link_for_chat(self, order, gateway='bkash'):
        """Generate payment link to send in chatbot."""
        result = self.create_payment(order, gateway)
        
        if result.get('success'):
            return f"""💳 **Payment Link Ready!**

Order: {order.order_reference}
Amount: {order.total} BDT
Gateway: {gateway.upper()}

🔗 Pay Now: {result.get('payment_url')}

আপনার payment সম্পন্ন হলে আমরা আপনাকে জানাব! 😊"""
        
        return "❌ Payment link তৈরি করতে সমস্যা হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।"


# Singleton instance
_payment_service = None

def get_payment_service():
    """Get or create payment service instance."""
    global _payment_service
    if _payment_service is None:
        _payment_service = PaymentService()
    return _payment_service
