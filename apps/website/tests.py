import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from apps.bookings.models import BookingSlot
from apps.website.models import GalleryImage, SafetyGuideline, PricingPackage
from apps.core.models import SiteSettings


class WebsitePublicViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.settings = SiteSettings.get_settings()
        self.slot1 = BookingSlot.objects.create(
            name='Slot 1 Morning Flight',
            start_time=datetime.time(9, 30),
            end_time=datetime.time(11, 30),
            max_capacity=6,
            is_active=True,
            order=1
        )
        self.package = PricingPackage.objects.create(
            name='Solo Falcon Flight',
            price=1499.00,
            features='Flight\nGear\nGuide',
            is_active=True
        )

    def test_01_customer_can_open_website(self):
        """Scenario 1: Customer can open the website."""
        response = self.client.get(reverse('website:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BLACK EAGLES")
        self.assertContains(response, "Experience the Thrill. Fly Beyond Limits.")

    def test_02_customer_can_access_booking_page(self):
        """Scenario 2: Customer can access the booking page."""
        response = self.client.get(reverse('bookings:booking_page'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Book Your Zipline Adventure")
        self.assertContains(response, "booking_date")

    def test_public_pages_render_correctly(self):
        """Checks about, gallery, safety, pricing, contact routes."""
        for route in ['website:about', 'website:gallery', 'website:safety', 'website:pricing', 'website:contact']:
            res = self.client.get(reverse(route))
            self.assertEqual(res.status_code, 200)
