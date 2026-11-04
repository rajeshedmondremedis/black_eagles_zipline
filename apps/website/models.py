from django.db import models


class GalleryImage(models.Model):
    """
    Administrator managed gallery photos with captions and category tags.
    """
    CATEGORY_CHOICES = [
        ('zipline', 'Zipline Aerial Action'),
        ('scenic', 'Scenic Mountain Views'),
        ('gear', 'Safety & Gear Fitting'),
        ('group', 'Group Adventures'),
    ]

    title = models.CharField(max_length=150)
    caption = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='gallery/')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='zipline')
    is_featured = models.BooleanField(default=False, help_text="Show in homepage featured preview")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Gallery Image"
        verbose_name_plural = "Gallery Images"

    def __str__(self):
        return self.title


class SafetyGuideline(models.Model):
    """
    Editable safety instructions, physical restrictions, health considerations,
    and equipment rules configured by the administrator for client review.
    """
    CATEGORY_CHOICES = [
        ('mandatory', 'Mandatory Safety Protocols'),
        ('restrictions', 'Weight & Age Restrictions (Configurable)'),
        ('health', 'Health & Medical Eligibility'),
        ('equipment', 'Gear & Equipment Guidelines'),
        ('responsibilities', 'Customer Responsibilities & Rider Conduct'),
    ]

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='mandatory')
    title = models.CharField(max_length=200)
    description = models.TextField(help_text="Detailed rules approved by Black Eagles administration")
    icon_name = models.CharField(max_length=50, default='shield-check', help_text="Bootstrap or Lucide icon name")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'order']
        verbose_name = "Safety Guideline"
        verbose_name_plural = "Safety Guidelines"

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title}"


class PricingPackage(models.Model):
    """
    Administrator configurable ticket tiers and pricing packages.
    """
    name = models.CharField(max_length=120)
    badge = models.CharField(max_length=80, blank=True, help_text="e.g. Most Popular, Weekend Special, Group Deal")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per ticket / person in INR")
    duration = models.CharField(max_length=80, default="Approx 45 - 60 mins")
    description = models.TextField(blank=True)
    features = models.TextField(
        help_text="Enter features separated by newlines (e.g. Full Course Flight, Safety Gear Included, Certified Guide)"
    )
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'price']
        verbose_name = "Pricing Package"
        verbose_name_plural = "Pricing Packages"

    def __str__(self):
        return f"{self.name} - ₹{self.price}"

    def feature_list(self):
        return [f.strip() for f in self.features.split('\n') if f.strip()]


class ContactMessage(models.Model):
    """
    Stores contact messages submitted by prospective riders and corporate visitors.
    """
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"

