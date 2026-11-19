import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.bookings.models import Booking, BookingSlot, Holiday

User = get_user_model()


class AdminDashboardTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='superadmin',
            email='super@blackeagleszipline.com',
            password='Password123!'
        )
        self.slot = BookingSlot.objects.create(
            name='Test Slot 1',
            start_time=datetime.time(10, 0),
            end_time=datetime.time(12, 0),
            max_capacity=6,
            is_active=True,
            order=1
        )
        today = timezone.localdate()
        self.target_date = today + datetime.timedelta(days=2)
        if self.target_date.weekday() == 2:
            self.target_date += datetime.timedelta(days=1)

        self.booking = Booking.objects.create(
            booking_reference='BEZ-2026-TEST01',
            full_name='Alice Wonderland',
            mobile_number='9876543210',
            email='alice@example.com',
            place='Bangalore',
            booking_date=self.target_date,
            slot=self.slot,
            number_of_members=2,
            status=Booking.Status.CONFIRMED
        )

    def test_20_unauthenticated_users_cannot_access_admin_pages(self):
        """Scenario 20: Unauthenticated users cannot access admin pages."""
        protected_urls = [
            reverse('dashboard:index'),
            reverse('dashboard:bookings_list'),
            reverse('dashboard:booking_detail', args=[self.booking.id]),
            reverse('dashboard:slots_list'),
            reverse('dashboard:holidays_list'),
            reverse('dashboard:settings_edit'),
            reverse('dashboard:gallery_manage'),
            reverse('dashboard:pricing_manage'),
            reverse('dashboard:safety_manage'),
            reverse('dashboard:api_search'),
            reverse('reports:reports_page'),
        ]

        for url in protected_urls:
            response = self.client.get(url)
            # Must redirect to login page
            self.assertEqual(response.status_code, 302, f"URL {url} is not protected!")
            self.assertIn(reverse('dashboard:login'), response.url)

    def test_non_staff_users_cannot_access_admin_pages(self):
        """Security Verification: Authenticated users without staff role are rejected."""
        regular_user = User.objects.create_user(
            username='regularrider',
            email='rider@example.com',
            password='Password123!',
            is_staff=False,
            is_superuser=False
        )
        self.client.force_login(regular_user)
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('dashboard:login'), response.url)

    def test_file_upload_security_restrictions(self):
        """Security Verification: Executable or non-image files are rejected from gallery."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_login(self.admin_user)

        fake_script = SimpleUploadedFile(
            "malicious.php",
            b"<?php echo 'attack'; ?>",
            content_type="application/x-php"
        )
        res = self.client.post(reverse('dashboard:gallery_manage'), {
            'action': 'add',
            'title': 'Exploit attempt',
            'category': 'zipline',
            'image': fake_script
        })
        self.assertEqual(res.status_code, 302)
        from apps.website.models import GalleryImage
        self.assertFalse(GalleryImage.objects.filter(title='Exploit attempt').exists())

    def test_15_admin_can_view_bookings(self):
        """Scenario 15: Admin can view bookings."""
        self.client.force_login(self.admin_user)

        # 1. Dashboard Index
        res = self.client.get(reverse('dashboard:index'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "BEZ-2026-TEST01")
        self.assertContains(res, "Alice Wonderland")

        # 2. Bookings List
        res_list = self.client.get(reverse('dashboard:bookings_list'))
        self.assertEqual(res_list.status_code, 200)
        self.assertContains(res_list, "Alice Wonderland")

        # 3. Booking Detail
        res_detail = self.client.get(reverse('dashboard:booking_detail', args=[self.booking.id]))
        self.assertEqual(res_detail.status_code, 200)
        self.assertContains(res_detail, "Alice Wonderland")
        self.assertContains(res_detail, "BEZ-2026-TEST01")

    def test_16_admin_can_manage_slots(self):
        """Scenario 16: Admin can manage slots."""
        self.client.force_login(self.admin_user)

        # 1. View slots
        res = self.client.get(reverse('dashboard:slots_list'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Test Slot 1")

        # 2. Edit slot name and capacity
        edit_url = reverse('dashboard:slot_edit', args=[self.slot.id])
        res_edit = self.client.post(edit_url, {
            'name': 'Updated Morning Zipline',
            'start_time': '10:00',
            'end_time': '12:00',
            'max_capacity': '8',
            'order': '1',
            'is_active': 'on'
        })
        self.assertEqual(res_edit.status_code, 302)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.name, 'Updated Morning Zipline')
        self.assertEqual(self.slot.max_capacity, 8)

        # 3. Toggle slot active status
        toggle_url = reverse('dashboard:slot_toggle', args=[self.slot.id])
        self.client.post(toggle_url)
        self.slot.refresh_from_db()
        self.assertFalse(self.slot.is_active)

    def test_17_admin_can_manage_holidays(self):
        """Scenario 17: Admin can manage holidays."""
        self.client.force_login(self.admin_user)

        # 1. View holidays page
        res = self.client.get(reverse('dashboard:holidays_list'))
        self.assertEqual(res.status_code, 200)

        # 2. Add holiday
        new_holiday_date = self.target_date + datetime.timedelta(days=7)
        res_add = self.client.post(reverse('dashboard:holidays_list'), {
            'action': 'add',
            'holiday_date': new_holiday_date.strftime('%Y-%m-%d'),
            'title': 'Test Maintenance Holiday',
            'description': 'Scheduled annual cable testing'
        })
        self.assertEqual(res_add.status_code, 302)
        holiday = Holiday.objects.filter(holiday_date=new_holiday_date).first()
        self.assertIsNotNone(holiday)
        self.assertEqual(holiday.title, 'Test Maintenance Holiday')

        # 3. Delete holiday
        res_del = self.client.post(reverse('dashboard:holidays_list'), {
            'action': 'delete',
            'holiday_id': holiday.id
        })
        self.assertEqual(res_del.status_code, 302)
        self.assertFalse(Holiday.objects.filter(id=holiday.id).exists())

    def test_spotlight_search_api(self):
        """Spotlight search API returns matching booking JSON."""
        self.client.force_login(self.admin_user)

        # Search by ref
        res = self.client.get(reverse('dashboard:api_search') + '?q=TEST01')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['reference'], 'BEZ-2026-TEST01')
        self.assertEqual(data['results'][0]['name'], 'Alice Wonderland')

        # Search by name
        res = self.client.get(reverse('dashboard:api_search') + '?q=Alice')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data['results']), 1)

        # Search short query < 2 chars returns empty list
        res = self.client.get(reverse('dashboard:api_search') + '?q=a')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()['results']), 0)


