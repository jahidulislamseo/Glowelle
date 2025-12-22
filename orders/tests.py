from django.test import TestCase
from django.contrib.auth import get_user_model
from products.models import Product, Category
from orders.models import Order, OrderItem
from users.models import Wallet

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
