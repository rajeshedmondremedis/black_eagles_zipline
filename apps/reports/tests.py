import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.bookings.models import Booking, BookingSlot

User = get_user_model()


class ReportsExportTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='reportadmin',
            email='reports@blackeagleszipline.com',
            password='Password123!'
        )
        self.slot = BookingSlot.objects.create(
            name='Report Slot',
            start_time=datetime.time(9, 30),
            end_time=datetime.time(11, 30),
            max_capacity=6,
            is_active=True,
            order=1
        )
        today = timezone.localdate()
        self.booking = Booking.objects.create(
            booking_reference='BEZ-2026-REP001',
            full_name='Report Rider',
            mobile_number='9876543210',
            email='reportrider@example.com',
            place='Cochin',
            booking_date=today,
            slot=self.slot,
            number_of_members=3,
            status=Booking.Status.CONFIRMED
        )

    def test_18_excel_report_downloads_correctly(self):
        """Scenario 18: Excel report downloads correctly."""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('reports:export_excel'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertIn('Black_Eagles_Zipline_Bookings_', response['Content-Disposition'])
        self.assertTrue(len(response.content) > 1000)

    def test_19_pdf_report_downloads_correctly(self):
        """Scenario 19: PDF report downloads correctly."""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('reports:export_pdf'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('Black_Eagles_Zipline_Manifest_', response['Content-Disposition'])
        # PDF files always start with %PDF
        self.assertTrue(response.content.startswith(b'%PDF'))
        self.assertTrue(len(response.content) > 1000)
