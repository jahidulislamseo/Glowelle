from django.db import models
from django.conf import settings
from products.models import Product

class Courier(models.Model):
    name = models.CharField(max_length=255, unique=True)
    website = models.URLField(null=True, blank=True)
    tracking_url_template = models.CharField(max_length=500, null=True, blank=True, help_text="e.g. https://courier.com/track?id={}")

    def __str__(self):
        return self.name

class PaymentGateway(models.Model):
    name = models.CharField(max_length=100) # e.g. bKash, Nagad
    logo = models.ImageField(upload_to='payments/', blank=True, null=True)
    account_number = models.CharField(max_length=50, help_text="e.g. 017xxxxxxxx")
    instructions = models.TextField(blank=True, help_text="Instructions for the user")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('cod', 'Cash on Delivery'),
        ('online', 'Online Payment'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    full_name = models.CharField(max_length=100, default="")
    email = models.EmailField(default="user@example.com")
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100, default="")
    zip_code = models.CharField(max_length=20, default="")
    
    total = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='cod')
    
    # Payment Details
    payment_gateway = models.ForeignKey(PaymentGateway, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)

    courier = models.ForeignKey(Courier, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    tracking_id = models.CharField(max_length=100, null=True, blank=True)
    coupon = models.ForeignKey('marketing.Coupon', on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = self.status

    def save(self, *args, **kwargs):
        # Check if status changed to 'cancelled' or 'returned' from a non-refunded state
        if self.pk and self.status in ['cancelled', 'returned'] and self._original_status not in ['cancelled', 'returned']:
            from products.models import StockLog
            
            # Restore stock
            for item in self.items.all():
                product = item.product
                product.stock_quantity += item.quantity
                # product.in_stock = True # Optional: Auto re-enable
                product.save()
                
                # Log the restoration
                StockLog.objects.create(
                    product=product,
                    quantity=item.quantity,
                    reason=f"Order #{self.id} {self.get_status_display()}"
                )
            
            # REFUND LOGIC (New)
            # Refund if Online Payment (any status change to cancel/return) OR if 'Returned' (implies paid)
            should_refund = False
            if self.payment_method == 'online':
                should_refund = True
            elif self.status == 'returned':
                should_refund = True
            
            if should_refund:
                from users.models import Wallet, WalletTransaction
                from decimal import Decimal
                
                wallet, _ = Wallet.objects.get_or_create(user=self.user)
                refund_amount = Decimal(str(self.total))
                wallet.balance += refund_amount
                wallet.save()
                
                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=refund_amount,
                    transaction_type='credit',
                    description=f"Refund for Order #{self.id} ({self.get_status_display()})"
                )
                
        super().save(*args, **kwargs)
        self._original_status = self.status

    def __str__(self):
        return f"Order #{self.id} by {self.user}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.FloatField()

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"
