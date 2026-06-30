import os
import shutil
from django.db import models
from django.conf import settings

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
        return getattr(self, 'title', getattr(self, 'name', 'Nyveralife'))
    
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
    site_title = models.CharField(max_length=200, default="Nyveralife")
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

    @property
    def messenger_username(self):
        """Parse facebook_url to get the profile ID/username for m.me link."""
        url = self.facebook_url
        if not url:
            url = "https://www.facebook.com/people/Nyvera-Life/61591039641335/"
        
        # Clean URL
        url = url.strip().rstrip('/')
        
        # If it has people/Name/ID format
        if '/people/' in url:
            parts = url.split('/')
            if parts[-1].isdigit():
                return parts[-1]
                
        # Standard username URL
        parts = url.split('/')
        last_part = parts[-1]
        if '?' in last_part:
            last_part = last_part.split('?')[0]
        return last_part

    def __str__(self):
        return "Website Configuration"

    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            return
        super(SiteSettings, self).save(*args, **kwargs)
        self._sync_logo_to_static()

    def _sync_logo_to_static(self):
        """Copy uploaded logo/favicon to static dirs so admin panel & favicon update automatically."""
        destinations = [
            settings.BASE_DIR / 'theme' / 'static' / 'images' / 'logo.png',
            settings.BASE_DIR / 'staticfiles' / 'images' / 'logo.png',
        ]
        src = self.favicon or self.logo
        if not src:
            return
        try:
            src_path = os.path.join(settings.MEDIA_ROOT, src.name)
            if not os.path.exists(src_path):
                return
            for dest in destinations:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(src_path, dest)
        except Exception:
            pass

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

