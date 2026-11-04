from django.shortcuts import render, redirect
from django.contrib import messages
from apps.website.models import GalleryImage, SafetyGuideline, PricingPackage
from apps.website.forms import ContactForm
from apps.core.models import SiteSettings


def home(request):
    settings = SiteSettings.get_settings()
    featured_gallery = GalleryImage.objects.filter(is_featured=True)[:6]
    if not featured_gallery.exists():
        featured_gallery = GalleryImage.objects.all()[:6]
    safety_highlights = SafetyGuideline.objects.filter(is_active=True)[:4]
    pricing_packages = PricingPackage.objects.filter(is_active=True)[:3]

    return render(request, 'website/home.html', {
        'settings': settings,
        'featured_gallery': featured_gallery,
        'safety_highlights': safety_highlights,
        'pricing_packages': pricing_packages,
    })


def about(request):
    settings = SiteSettings.get_settings()
    safety_highlights = SafetyGuideline.objects.filter(is_active=True)[:3]
    return render(request, 'website/about.html', {
        'settings': settings,
        'safety_highlights': safety_highlights,
    })


def gallery(request):
    category = request.GET.get('category')
    images = GalleryImage.objects.all()
    if category and category in dict(GalleryImage.CATEGORY_CHOICES):
        images = images.filter(category=category)
    categories = GalleryImage.CATEGORY_CHOICES
    return render(request, 'website/gallery.html', {
        'images': images,
        'categories': categories,
        'active_category': category,
    })


def safety(request):
    guidelines_by_cat = {}
    for cat_key, cat_name in SafetyGuideline.CATEGORY_CHOICES:
        items = SafetyGuideline.objects.filter(category=cat_key, is_active=True)
        if items.exists():
            guidelines_by_cat[cat_name] = items

    return render(request, 'website/safety.html', {
        'guidelines_by_cat': guidelines_by_cat,
    })


def pricing(request):
    packages = PricingPackage.objects.filter(is_active=True)
    return render(request, 'website/pricing.html', {
        'packages': packages,
    })


def contact(request):
    settings = SiteSettings.get_settings()
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you! Your message has been received. Our team will get back to you shortly.")
            return redirect('website:contact')
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        form = ContactForm()

    return render(request, 'website/contact.html', {
        'settings': settings,
        'form': form,
    })
