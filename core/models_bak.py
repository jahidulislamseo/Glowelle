from django.db import models

# EMERGENCY FIX: Dummy class to satisfy ghost import
class AnalyticsSettings(models.Model):
    pass

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
