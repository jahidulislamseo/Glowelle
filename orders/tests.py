from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from products.models import Product, Category
from orders.models import Order, OrderItem
from users.models import Wallet
from marketing.models import Coupon

User = get_user_model()

class OrderLogicTest(TestCase):
    def setUp(self):
        # Create User & Wallet
        self.user = User.objects.create_user(username='testuser', password='password123', email='test@example.com')
        self.wallet = Wallet.objects.create(user=self.user, balance=0.00)
        
        # Create Product
        self.category = Category.objects.create(name='Test Category', slug='test-cat')
        self.product = Product.objects.create(
            title='Test Product', slug='test-prod', category=self.category,
            price=100.00, stock_quantity=10, in_stock=True
        )

    def test_stock_restoration_on_cancel(self):
        """Test if stock is restored when order is cancelled"""
        # Create Order
        order = Order.objects.create(user=self.user, total=200.00, status='pending')
        OrderItem.objects.create(order=order, product=self.product, quantity=2, price=100.00)
        
        # Simulate Purchase (stock reduction usually happens at checkout view, but here we manually reduce to simulate state)
        self.product.stock_quantity = 8 
        self.product.save()
        
        # Cancel Order
        order.status = 'cancelled'
        order.save()
        
        # Reload Product
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 10)

    def test_wallet_refund_on_online_cancel(self):
        """Test if money is refunded to wallet for online orders"""
        self.wallet.balance = 1000.00
        self.wallet.save()
        
        # Order paid online
        order = Order.objects.create(
            user=self.user, total=200.00, status='pending', 
            payment_method='online'
        )
        
        # Trigger Refund
        order.status = 'cancelled'
        order.save()
        
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 1200.00) # 1000 + 200

    def test_wallet_refund_on_return(self):
        """Test if money is refunded when order is returned (even COD considered paid if delivered then returned)"""
        # COD Order delivered then returned
        order = Order.objects.create(
            user=self.user, total=500.00, status='delivered',
            payment_method='cod'
        )
        
        # Return Order
        order.status = 'returned'
        order.save()
        
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 500.00) # 0 + 500

class CouponViewTest(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.valid_coupon = Coupon.objects.create(
            code='SAVE10',
            discount_percent=10,
            valid_from=self.now - timedelta(days=1),
            valid_to=self.now + timedelta(days=1),
            active=True
        )
        self.expired_coupon = Coupon.objects.create(
            code='EXPIRED',
            discount_percent=10,
            valid_from=self.now - timedelta(days=5),
            valid_to=self.now - timedelta(days=1),
            active=True
        )
        self.inactive_coupon = Coupon.objects.create(
            code='INACTIVE',
            discount_percent=10,
            valid_from=self.now - timedelta(days=1),
            valid_to=self.now + timedelta(days=1),
            active=False
        )
        self.future_coupon = Coupon.objects.create(
            code='FUTURE',
            discount_percent=10,
            valid_from=self.now + timedelta(days=1),
            valid_to=self.now + timedelta(days=2),
            active=True
        )

    def test_coupon_apply_success(self):
        """Test applying a valid coupon"""
        response = self.client.post(reverse('coupon_apply'), {'code': 'SAVE10'}, follow=True)
        self.assertRedirects(response, reverse('cart_detail'))
        self.assertEqual(self.client.session.get('coupon_id'), self.valid_coupon.id)
        # Check for success message
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Coupon 'SAVE10' applied successfully!")

    def test_coupon_apply_invalid_code(self):
        """Test applying a non-existent coupon code"""
        response = self.client.post(reverse('coupon_apply'), {'code': 'NONEXISTENT'}, follow=True)
        self.assertRedirects(response, reverse('cart_detail'))
        self.assertIsNone(self.client.session.get('coupon_id'))
        # Check for error message
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Invalid or expired coupon code.")

    def test_coupon_apply_inactive(self):
        """Test applying an inactive coupon"""
        response = self.client.post(reverse('coupon_apply'), {'code': 'INACTIVE'}, follow=True)
        self.assertRedirects(response, reverse('cart_detail'))
        self.assertIsNone(self.client.session.get('coupon_id'))
        # Check for error message
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Invalid or expired coupon code.")

    def test_coupon_apply_expired(self):
        """Test applying an expired coupon"""
        response = self.client.post(reverse('coupon_apply'), {'code': 'EXPIRED'}, follow=True)
        self.assertRedirects(response, reverse('cart_detail'))
        self.assertIsNone(self.client.session.get('coupon_id'))
        # Check for error message
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Invalid or expired coupon code.")

    def test_coupon_apply_future(self):
        """Test applying a coupon that is not yet valid"""
        response = self.client.post(reverse('coupon_apply'), {'code': 'FUTURE'}, follow=True)
        self.assertRedirects(response, reverse('cart_detail'))
        self.assertIsNone(self.client.session.get('coupon_id'))
        # Check for error message
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Invalid or expired coupon code.")

    def test_coupon_apply_no_code(self):
        """Test submitting the coupon form without a code"""
        # Set a coupon in session first to see if it remains
        session = self.client.session
        session['coupon_id'] = self.valid_coupon.id
        session.save()

        response = self.client.post(reverse('coupon_apply'), {'code': ''}, follow=True)
        self.assertRedirects(response, reverse('cart_detail'))
        # Should still have the old coupon id because if not code, it does nothing
        self.assertEqual(self.client.session.get('coupon_id'), self.valid_coupon.id)
