from django.contrib import admin
from apps.website.models import GalleryImage, SafetyGuideline, PricingPackage, ContactMessage


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_featured', 'order', 'created_at')
    list_filter = ('category', 'is_featured')
    search_fields = ('title', 'caption')


@admin.register(SafetyGuideline)
class SafetyGuidelineAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_active', 'order')
    list_filter = ('category', 'is_active')
    search_fields = ('title', 'description')


@admin.register(PricingPackage)
class PricingPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration', 'badge', 'is_featured', 'is_active', 'order')
    list_filter = ('is_active', 'is_featured')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'subject', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'phone', 'subject', 'message')
