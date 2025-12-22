from django.db import models
from django.conf import settings

class VisitorSession(models.Model):
    session_key = models.CharField(max_length=40, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    device_type = models.CharField(max_length=20, default='desktop') # mobile, tablet, desktop
    os = models.CharField(max_length=50, null=True, blank=True)
    browser = models.CharField(max_length=50, null=True, blank=True)
    
    country = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    
    # Time Tracking
    start_time = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    
    # Calculated fields
    is_bounce = models.BooleanField(default=True) # True if only 1 page view
    
    def __str__(self):
        return f"Session {self.session_key} ({self.start_time.strftime('%Y-%m-%d %H:%M')})"

class PageView(models.Model):
    session = models.ForeignKey(VisitorSession, on_delete=models.CASCADE, related_name='page_views')
    url = models.CharField(max_length=1000)
    referer = models.CharField(max_length=1000, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    response_time_ms = models.IntegerField(default=0)
    status_code = models.IntegerField(default=200)
    method = models.CharField(max_length=10, default='GET')
    
    def __str__(self):
        return f"{self.method} {self.url}"

class AnalyticsEvent(models.Model):
    EVENT_TYPES = (
        ('search', 'Search'),
        ('add_to_cart', 'Add to Cart'),
        ('remove_from_cart', 'Remove from Cart'),
        ('checkout_start', 'Checkout Started'),
        ('checkout_step', 'Checkout Step'),
        ('payment_success', 'Payment Success'),
        ('payment_failed', 'Payment Failed'),
        ('login', 'Login'),
        ('signup', 'Signup'),
        ('logout', 'Logout'),
        ('error_404', '404 Error'),
        ('out_of_stock_click', 'Out of Stock Click'),
        ('wishlist_add', 'Wishlist Add'),
        ('coupon_used', 'Coupon Used'),
    )
    
    session = models.ForeignKey(VisitorSession, on_delete=models.CASCADE, related_name='events')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    value = models.CharField(max_length=255, null=True, blank=True) # e.g. search term, product ID
    metadata = models.JSONField(null=True, blank=True) # Extra data
    timestamp = models.DateTimeField(auto_now_add=True)
    url = models.CharField(max_length=1000, null=True, blank=True)

    def __str__(self):
        return f"{self.event_type} - {self.value}"
