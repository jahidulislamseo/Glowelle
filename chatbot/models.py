from django.db import models

class ChatbotFAQ(models.Model):
    question = models.CharField(max_length=255, help_text="Common user question")
    keywords = models.CharField(max_length=255, help_text="Comma-separated keywords to trigger this answer")
    answer = models.TextField(help_text="The response the chatbot should give")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.question

    class Meta:
        verbose_name = "Chatbot FAQ"
        verbose_name_plural = "Chatbot FAQs"
        ordering = ['question']
        db_table = 'core_chatbotfaq'

class ChatbotSettings(models.Model):
    welcome_message = models.TextField(
        default="👋 Hi! Welcome to GlowElle! How can I help you today?",
        help_text="First message shown when the chat opens"
    )
    system_prompt = models.TextField(
        default="You are 'GlowElle Assistant'. Be helpful, confident, and professional. Use product data provided. Guarantee 100% freshness.",
        help_text="Global instructions for the AI brain"
    )
    not_found_message = models.TextField(
        default="I couldn't find a specific answer for that. Would you like to talk to a human agent?",
        help_text="Fall-back message when no FAQ or product matches"
    )

    # Working Hours
    working_hours_start = models.TimeField(default="09:00", help_text="Support start time (e.g., 09:00)")
    working_hours_end = models.TimeField(default="22:00", help_text="Support end time (e.g., 22:00)")
    offline_message = models.TextField(
        default="Our support team is currently offline. Please leave your message and we will get back to you during working hours (9 AM - 10 PM).",
        help_text="Message shown when user asks for human support outside working hours"
    )

    # Promotions
    promo_message = models.TextField(blank=True, help_text="Special offer or announcement (e.g., '10% off on all fruits today!')")
    is_promo_active = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Chatbot Settings"
        verbose_name_plural = "Chatbot Settings"
        db_table = 'core_chatbotsettings'

    def __str__(self):
        return "Chatbot Configuration"

    def save(self, *args, **kwargs):
        if not self.pk and ChatbotSettings.objects.exists():
            return
        super(ChatbotSettings, self).save(*args, **kwargs)

class ChatbotSuggestion(models.Model):
    text = models.CharField(max_length=50, help_text="Button text (e.g., 'Popular Items')")
    action = models.CharField(max_length=50, default="message", help_text="Action type (message/url)")
    value = models.CharField(max_length=255, blank=True, help_text="Value for the action (e.g., the message to send)")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Chatbot Suggestion"
        db_table = 'core_chatbotsuggestion'

    def __str__(self):
        return self.text

class ChatbotIntent(models.Model):
    intent_key = models.CharField(max_length=50, unique=True, help_text="The internal key (e.g., 'buying', 'support')")
    display_name = models.CharField(max_length=100)
    keywords = models.TextField(help_text="Comma-separated keywords to trigger this intent")
    is_active = models.BooleanField(default=True, help_text="Whether this intent is active")
    
    class Meta:
        verbose_name = "Chatbot Intent"
        verbose_name_plural = "Chatbot Intents"
        db_table = 'core_chatbotintent'

    def __str__(self):
        return self.display_name

class ChatbotConversationMemory(models.Model):
    """
    Tracks conversation history and user preferences for memory-based learning.
    """
    session_id = models.CharField(max_length=255, db_index=True, help_text="Unique session identifier")
    user_message = models.TextField(help_text="User's message")
    bot_response = models.TextField(help_text="Bot's response")
    detected_intent = models.CharField(max_length=50, blank=True, help_text="Detected intent (greeting, product_query, etc.)")
    
    # User preferences (stored as JSON)
    user_preferences = models.JSONField(
        default=dict, 
        blank=True,
        help_text="User preferences like last_product, language, etc."
    )
    
    # Greeting counter
    greeting_count = models.IntegerField(default=0, help_text="Number of times user greeted in this session")
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = "Conversation Memory"
        verbose_name_plural = "Conversation Memories"
        db_table = 'chatbot_conversation_memory'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_id', '-created_at'], name='session_created_idx'),
        ]
    
    def __str__(self):
        return f"Session {self.session_id} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

# Import analytics models
from .analytics_models import ChatbotAnalytics, ChatbotMetric, PopularProduct
