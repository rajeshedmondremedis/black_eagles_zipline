from django.db import models


class SiteSettings(models.Model):
    """
    Singleton model to store all administrator-configurable business details,
    contact info, social links, and website copy without touching code.
    """
    site_name = models.CharField(max_length=150, default="Black Eagles Zipline")
    tagline = models.CharField(max_length=255, default="Experience the Thrill. Fly Beyond Limits.")
    hero_heading = models.CharField(max_length=255, default="Experience the Thrill. Fly Beyond Limits.")
    hero_subheading = models.TextField(
        default="Soar high above emerald canopies and rugged canyons. Black Eagles Zipline brings you world-class adventure tourism engineered with certified safety and untamed excitement."
    )
    
    # Business Contact Information
    phone_number = models.CharField(max_length=50, default="+91 98765 43210")
    whatsapp_number = models.CharField(max_length=50, default="+91 98765 43210")
    email_address = models.EmailField(default="contact@blackeagleszipline.com")
    address = models.TextField(
        default="Eagle Point Ridge, Cliffside Forest Reserve, Western Ghats, India"
    )
    google_maps_embed_url = models.TextField(
        default="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3907.5645512217997!2d76.126584!3d11.660144!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMTHCsDM5JzM2LjUiTiA3NsKwMDcnMzUuNyJF!5e0!3m2!1sen!2sin!4v1700000000000!5m2!1sen!2sin",
        help_text="Paste iframe source URL from Google Maps Embed"
    )
    
    # Social Media Links
    facebook_url = models.URLField(blank=True, default="https://facebook.com")
    instagram_url = models.URLField(blank=True, default="https://instagram.com")
    youtube_url = models.URLField(blank=True, default="https://youtube.com")
    twitter_url = models.URLField(blank=True, default="https://twitter.com")
    
    # About Content
    about_summary = models.TextField(
        default="Black Eagles Zipline is an elite outdoor adventure destination engineered for travelers, adrenaline enthusiasts, and families who seek an unforgettable bird's-eye voyage through nature."
    )
    about_story = models.TextField(
        default="Founded with a passion for wilderness conservation and exhilarating aerial sport, Black Eagles Zipline combines dual-cable military-grade engineering with certified safety guides. Spanning over multiple kilometers of breathtaking valley spans, each flight is meticulously monitored and inspected daily to deliver absolute thrill with zero compromise on safety."
    )
    
    # Safety Overview Summary
    safety_overview = models.TextField(
        default="Safety is our absolute cornerstone. Every flight harnesses imported CE/UIAA certified harnesses, double-pulley brake backups, and redundant anchor systems inspected by certified structural safety engineers every morning."
    )
    
    # Working Hours description
    operating_hours = models.CharField(max_length=150, default="Thursday to Tuesday: 09:00 AM - 06:30 PM (Closed Wednesdays)")
    closed_day_notice = models.CharField(max_length=150, default="Wednesday Routine Maintenance & Structural Inspections")
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return f"{self.site_name} Configuration"

    @classmethod
    def get_settings(cls):
        settings, created = cls.objects.get_or_create(id=1)
        return settings
