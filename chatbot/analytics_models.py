from django.db import models
from django.utils import timezone

class ChatbotAnalytics(models.Model):
    """
    Daily analytics summary for chatbot performance.
    """
    date = models.DateField(default=timezone.now, unique=True, db_index=True)
    total_conversations = models.IntegerField(default=0, help_text="Total chat sessions started")
    total_messages = models.IntegerField(default=0, help_text="Total messages exchanged")
    total_orders = models.IntegerField(default=0, help_text="Orders placed via chatbot")
    conversion_rate = models.FloatField(default=0.0, help_text="Percentage of chats that resulted in orders")
    average_messages_per_session = models.FloatField(default=0.0)
    unique_users = models.IntegerField(default=0, help_text="Unique users who chatted")
    
    class Meta:
        verbose_name = "Chatbot Analytics"
        verbose_name_plural = "Chatbot Analytics"
        db_table = 'chatbot_analytics'
        ordering = ['-date']
    
    def __str__(self):
        return f"Analytics for {self.date}"
    
    def calculate_metrics(self):
        """Recalculate all metrics for this date."""
        from .models import ChatbotMetric
        
        metrics = ChatbotMetric.objects.filter(started_at__date=self.date)
        
        self.total_conversations = metrics.count()
        self.total_messages = sum(m.messages_count for m in metrics)
        self.total_orders = metrics.filter(resulted_in_order=True).count()
        
        if self.total_conversations > 0:
            self.conversion_rate = (self.total_orders / self.total_conversations) * 100
            self.average_messages_per_session = self.total_messages / self.total_conversations
        
        # Count unique users (by session_id prefix if user_id not available)
        self.unique_users = metrics.values('session_id').distinct().count()
        
        self.save()

class ChatbotMetric(models.Model):
    """
    Individual chat session metrics.
    """
    session_id = models.CharField(max_length=255, db_index=True)
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    messages_count = models.IntegerField(default=0)
    resulted_in_order = models.BooleanField(default=False)
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
    user_rating = models.IntegerField(null=True, blank=True, help_text="1-5 stars")
    detected_intents = models.JSONField(default=list, blank=True, help_text="List of intents detected")
    
    class Meta:
        verbose_name = "Chat Session Metric"
        verbose_name_plural = "Chat Session Metrics"
        db_table = 'chatbot_metrics'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['session_id', '-started_at'], name='session_time_idx'),
            models.Index(fields=['resulted_in_order', '-started_at'], name='order_time_idx'),
        ]
    
    def __str__(self):
        return f"Session {self.session_id[:8]} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"
    
    def mark_order_placed(self, order):
        """Mark this session as resulted in an order."""
        self.resulted_in_order = True
        self.order = order
        self.save()
        
        # Update daily analytics
        analytics, created = ChatbotAnalytics.objects.get_or_create(
            date=self.started_at.date()
        )
        analytics.calculate_metrics()

class PopularProduct(models.Model):
    """
    Track popular products via chatbot.
    """
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now, db_index=True)
    query_count = models.IntegerField(default=0, help_text="Times queried in chatbot")
    order_count = models.IntegerField(default=0, help_text="Times ordered via chatbot")
    
    class Meta:
        verbose_name = "Popular Product"
        verbose_name_plural = "Popular Products"
        db_table = 'chatbot_popular_products'
        unique_together = ('product', 'date')
        ordering = ['-date', '-query_count']
    
    def __str__(self):
        return f"{self.product.title} - {self.date}"
