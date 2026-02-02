from django.db import models

class SEOModel(models.Model):
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.CharField(max_length=255, blank=True, null=True, help_text="Comma-separated keywords for SEO")
    og_image = models.ImageField(upload_to='seo/', max_length=255, blank=True, null=True, help_text="Image for social media sharing")
    
    class Meta:
        abstract = True
    
    def get_meta_title(self):
        """Return meta_title if set, otherwise fall back to the model's primary field"""
        if self.meta_title:
            return self.meta_title
        # Fallback to 'title' or 'name' attribute if available
        return getattr(self, 'title', getattr(self, 'name', 'Al Barakah Mart'))
    
    def get_meta_description(self):
        """Return meta_description if set, otherwise fall back to description field"""
        if self.meta_description:
            return self.meta_description
        # Fallback to 'description' attribute if available
        desc = getattr(self, 'description', '')
        if desc:
            # Strip HTML and truncate
            from django.utils.html import strip_tags
            return strip_tags(desc)[:160]
        return 'Fresh organic groceries delivered to your doorstep in Dhaka.'

class SiteSettings(models.Model):
    site_title = models.CharField(max_length=200, default="Al Barakah Mart")
    meta_description = models.TextField(blank=True, help_text="SEO description for the homepage")
    
    # Analytics
    ga4_tracking_id = models.CharField(max_length=50, blank=True, help_text="e.g., G-XXXXXXXXXX")
    search_console_code = models.CharField(max_length=100, blank=True, help_text="Google verification code")
    
    # Contact (Optional based on user)
    # Contact (Optional based on user)
    support_email = models.EmailField(blank=True)
    support_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True, help_text="Full address (e.g. House 123, Road 4, Dhaka)")
    
    # Branding
    logo = models.ImageField(upload_to='branding/', blank=True, null=True, help_text="Site Logo (Recommended height: 50px)")
    favicon = models.ImageField(upload_to='branding/', blank=True, null=True, help_text="Browser Tab Icon (Recommended: 32x32px)")
    
    # Social Media
    facebook_url = models.URLField(blank=True, help_text="Facebook Page URL")
    instagram_url = models.URLField(blank=True, help_text="Instagram Profile URL")
    twitter_url = models.URLField(blank=True, help_text="Twitter/X Profile URL")
    youtube_url = models.URLField(blank=True, help_text="YouTube Channel URL")
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return "Website Configuration"

    def save(self, *args, **kwargs):
        # Singleton pattern: ensure only one instance exists
        if not self.pk and SiteSettings.objects.exists():
            return
        super(SiteSettings, self).save(*args, **kwargs)

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} ({self.created_at.strftime('%Y-%m-%d')})"

    class Meta:
        ordering = ['-created_at']

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

class ChatbotSettings(models.Model):
    welcome_message = models.TextField(
        default="👋 Hi! Welcome to Al Barakah Mart! How can I help you today?",
        help_text="First message shown when the chat opens"
    )
    system_prompt = models.TextField(
        default="You are 'Al Barakah Assistant'. Be helpful, confident, and professional. Use product data provided. Guarantee 100% freshness.",
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

    def __str__(self):
        return self.text

class ChatbotIntent(models.Model):
    intent_key = models.CharField(max_length=50, unique=True, help_text="The internal key (e.g., 'buying', 'support')")
    display_name = models.CharField(max_length=100)
    keywords = models.TextField(help_text="Comma-separated keywords to trigger this intent")
    class Meta:
        verbose_name = "Chatbot Intent"
        verbose_name_plural = "Chatbot Intents"

    def __str__(self):
        return self.display_name
