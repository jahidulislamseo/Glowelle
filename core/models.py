from django.db import models

class SEOModel(models.Model):
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.CharField(max_length=255, blank=True, null=True, help_text="Comma-separated keywords for SEO")
    og_image = models.ImageField(upload_to='seo/', blank=True, null=True, help_text="Image for social media sharing")
    
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
    support_email = models.EmailField(blank=True)
    support_phone = models.CharField(max_length=20, blank=True)
    
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
