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
    RETURN_STATUS_CHOICES = (
        ('none', 'None'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    )
    REFUND_STATUS_CHOICES = (
        ('none', 'None'),
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('cod', 'Cash on Delivery'),
        ('online', 'Online Payment'),
    )
    SOURCE_CHOICES = (
        ('website', 'Website'),
        ('mobile_web', 'Mobile Web'),
        ('app', 'Mobile App'),
        ('admin', 'Admin Manual Entry'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('refunded', 'Refunded'),
    )

    # 1. Order Identity
    # id is auto-created
    order_reference = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="Unique reference number")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='website')
    
    # 2. Order Status & Timeline (Status is already there)
    estimated_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateTimeField(null=True, blank=True)
    
    # 3. Customer Information (User link is there)
    # Storing snapshot of address at time of order is better than just reference
    full_name = models.CharField(max_length=100, default="")
    email = models.EmailField(default="user@example.com")
    phone = models.CharField(max_length=20)
    
    # Delivery Address
    address = models.TextField(help_text="Delivery Address")
    city = models.CharField(max_length=100, default="")
    zip_code = models.CharField(max_length=20, default="")
    
    # Billing Address
    billing_address = models.TextField(blank=True, null=True)
    billing_city = models.CharField(max_length=100, blank=True, null=True)
    billing_zip_code = models.CharField(max_length=20, blank=True, null=True)
    
    # 5. Pricing & Calculation
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    extra_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Any extra fees")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00) # Changed to Decimal for accuracy
    
    coupon = models.ForeignKey('marketing.Coupon', on_delete=models.SET_NULL, null=True, blank=True)
    
    # 6. Payment Information
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='cod')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    payment_gateway = models.ForeignKey(PaymentGateway, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    payment_attempt_count = models.IntegerField(default=0)
    
    # 7. Delivery & Courier
    courier = models.ForeignKey(Courier, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    tracking_id = models.CharField(max_length=100, null=True, blank=True)
    shipping_label = models.FileField(upload_to='shipping_labels/', null=True, blank=True)
    delivery_note = models.TextField(blank=True, null=True, help_text="Note from customer for delivery")
    
    # 8. Cancellation, Return, Refund
    cancellation_reason = models.TextField(blank=True, null=True)
    return_reason = models.TextField(blank=True, null=True)
    return_status = models.CharField(max_length=20, choices=RETURN_STATUS_CHOICES, default='none')
    
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    refund_date = models.DateTimeField(null=True, blank=True)
    refund_status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='none')
    refund_method = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. bKash, Bank Transfer")
    
    # 9. Documents
    invoice_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    invoice_download_count = models.IntegerField(default=0)
    credit_note_number = models.CharField(max_length=50, blank=True, null=True)

    
    # 10. Admin Controls
    internal_admin_note = models.TextField(blank=True, null=True, help_text="Private note for admins")
    
    # 13. Support & Communication
    support_ticket = models.ForeignKey('users.SupportTicket', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    
    # 11. Admin Logs & Security
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_orders')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_orders')
    
    # 12. Analytics & Flags
    is_high_risk = models.BooleanField(default=False)
    risk_score = models.IntegerField(default=0)
    is_repeat_order = models.BooleanField(default=False)
    profit_estimate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # 14. System & Automation
    is_confirmation_email_sent = models.BooleanField(default=False)
    is_delivery_update_sent = models.BooleanField(default=False)
    automation_logs = models.TextField(blank=True, null=True, help_text="JSON or text logs of automation")

    # 15. Final System States
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    is_archived = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at'], name='order_user_created_idx'),
            models.Index(fields=['status', '-created_at'], name='order_status_created_idx'),
            models.Index(fields=['payment_status', 'status'], name='order_payment_status_idx'),
            models.Index(fields=['-created_at'], name='order_created_idx'),
        ]

    @property
    def order_value_category(self):
        if self.total > 5000:
            return 'High'
        elif self.total > 1000:
            return 'Medium'
        return 'Low'


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = self.status

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        # Generate Reference & Invoice if missing
        if not self.order_reference:
            import uuid
            self.order_reference = str(uuid.uuid4())[:8].upper()
            
        if not self.invoice_number:
            self.invoice_number = f"INV-{self.order_reference}"

        # Check if status changed
        status_changed = False
        if not is_new and self.status != self._original_status:
            status_changed = True
            
        # Check if status changed to 'cancelled' or 'returned' from a non-refunded state
        if self.pk and self.status in ['cancelled', 'returned'] and self._original_status not in ['cancelled', 'returned']:
            # Restore stock (Atomic update)
            for item in self.items.all():
                from products.models import Product, StockLog
                
                Product.objects.filter(id=item.product.id).update(stock_quantity=models.F('stock_quantity') + item.quantity)
                
                # Log the restoration
                StockLog.objects.create(
                    product=item.product,
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
                try:
                    # refund_amount = Decimal(str(self.total)) # self.total is now Decimal
                    refund_amount = self.total
                    wallet.balance += refund_amount
                    wallet.save()
                    
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        amount=refund_amount,
                        transaction_type='credit',
                        description=f"Refund for Order #{self.id} ({self.get_status_display()})"
                    )
                    self.refund_amount = refund_amount
                    self.payment_status = 'refunded'
                except Exception as e:
                    print(f"Refund error: {e}")
                
        super().save(*args, **kwargs)
        
        # Log Status Change
        if is_new or status_changed:
            OrderStatusHistory.objects.create(
                order=self,
                status=self.status,
                created_by=self.updated_by, # Assuming updated_by is set in view/admin
                description=f"Order marked as {self.get_status_display()}"
            )
            
            # Send notification on status change
            if status_changed:
                try:
                    from chatbot.notification_service import send_order_notification
                    send_order_notification(self, status_change=True)
                except Exception as e:
                    print(f"Notification error: {e}")
            
        self._original_status = self.status

    def __str__(self):
        return f"Order #{self.id} ({self.order_reference})"

class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Order Status History"
        verbose_name_plural = "Order Status History"

    def __str__(self):
        return f"{self.order.id} - {self.status}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey('products.ProductVariant', on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2) # Changed to Decimal
    stock_at_order = models.IntegerField(null=True, blank=True, help_text="Stock quantity at the time of order")
    
    def get_total(self):
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        if not self.pk and not self.stock_at_order and self.product:
            self.stock_at_order = self.product.stock_quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"
