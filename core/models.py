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
        return getattr(self, 'title', getattr(self, 'name', 'GlowElle'))
    
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
        return 'Your one-stop shop for fresh organic fruits, vegetables, meat, and daily essentials.'

class SiteSettings(models.Model):
    site_title = models.CharField(max_length=200, default="GlowElle")
    meta_description = models.TextField(default="Your one-stop shop for fresh organic fruits, vegetables, meat, and daily essentials.", blank=True, help_text="SEO description for the homepage")
    
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

class ErrorLog(models.Model):
    LEVEL_CHOICES = [
        ('ERROR', 'Error'),
        ('WARNING', 'Warning'),
        ('CRITICAL', 'Critical'),
    ]

    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='ERROR', db_index=True)
    message = models.TextField()
    traceback = models.TextField(blank=True)
    path = models.CharField(max_length=500, blank=True)
    method = models.CharField(max_length=10, blank=True)
    user = models.CharField(max_length=150, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_resolved = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Error Log'
        verbose_name_plural = 'Error Logs'

    def __str__(self):
        return f"[{self.level}] {self.message[:80]} — {self.created_at.strftime('%Y-%m-%d %H:%M')}"


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

