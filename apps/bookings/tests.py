import datetime
import threading
from django.db import models
from django.test import TestCase, Client, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.bookings.models import Booking, BookingSlot, Holiday
from apps.bookings.services import (
    validate_booking_date,
    get_available_slots_for_date,
    create_booking_atomic,
    cancel_booking_atomic,
    modify_booking_atomic
)


class BookingEngineTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create 4 configurable slots
        self.slot1 = BookingSlot.objects.create(
            name='Slot 1 Morning Flight',
            start_time=datetime.time(9, 30),
            end_time=datetime.time(11, 30),
            max_capacity=6,
            is_active=True,
            order=1
        )
        self.slot2 = BookingSlot.objects.create(
            name='Slot 2 Midday Rush',
            start_time=datetime.time(11, 45),
            end_time=datetime.time(13, 45),
            max_capacity=6,
            is_active=True,
            order=2
        )
        self.slot3 = BookingSlot.objects.create(
            name='Slot 3 Afternoon Canopy',
            start_time=datetime.time(14, 15),
            end_time=datetime.time(16, 15),
            max_capacity=6,
            is_active=True,
            order=3
        )
        self.slot4 = BookingSlot.objects.create(
            name='Slot 4 Sunset Flight',
            start_time=datetime.time(16, 30),
            end_time=datetime.time(18, 30),
            max_capacity=6,
            is_active=True,
            order=4
        )

        # Helper to find a non-Wednesday future date
        today = timezone.localdate()
        self.valid_date = today + datetime.timedelta(days=2)
        if self.valid_date.weekday() == 2:  # Wednesday
            self.valid_date += datetime.timedelta(days=1)

    def test_03_customer_can_select_valid_date(self):
        """Scenario 3: Customer can select a valid date."""
        is_valid, msg, holiday = validate_booking_date(self.valid_date)
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")

        res = self.client.get(f"{reverse('bookings:api_availability')}?date={self.valid_date.strftime('%Y-%m-%d')}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['is_holiday'])
        self.assertEqual(len(data['slots']), 4)

    def test_04_wednesday_booking_is_blocked(self):
        """Scenario 4: Wednesday booking is blocked."""
        # Find next Wednesday
        today = timezone.localdate()
        days_ahead = (2 - today.weekday() + 7) % 7
        if days_ahead == 0:
            days_ahead = 7
        wednesday_date = today + datetime.timedelta(days=days_ahead)
        self.assertEqual(wednesday_date.weekday(), 2)

        is_valid, msg, _ = validate_booking_date(wednesday_date)
        self.assertFalse(is_valid)
        self.assertIn("Sorry! Bookings are not available on this date", msg)

        # Also verify AJAX API
        res = self.client.get(f"{reverse('bookings:api_availability')}?date={wednesday_date.strftime('%Y-%m-%d')}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data['success'])
        self.assertTrue(data['is_holiday'])

        # Verify POST booking fails
        with self.assertRaises(ValidationError):
            create_booking_atomic(
                full_name='Test Rider',
                mobile_number='9876543210',
                email='rider@example.com',
                place='Bangalore',
                booking_date=wednesday_date,
                slot_id=self.slot1.id,
                number_of_members=2
            )

    def test_05_past_date_booking_is_blocked(self):
        """Scenario 5: Past date booking is blocked."""
        past_date = timezone.localdate() - datetime.timedelta(days=1)
        is_valid, msg, _ = validate_booking_date(past_date)
        self.assertFalse(is_valid)
        self.assertIn("Past dates cannot be selected", msg)

        with self.assertRaises(ValidationError):
            create_booking_atomic(
                full_name='Test Rider',
                mobile_number='9876543210',
                email='rider@example.com',
                place='Bangalore',
                booking_date=past_date,
                slot_id=self.slot1.id,
                number_of_members=1
            )

    def test_06_admin_defined_holiday_booking_is_blocked(self):
        """Scenario 6: Admin-defined holiday booking is blocked."""
        holiday_date = self.valid_date + datetime.timedelta(days=1)
        if holiday_date.weekday() == 2:
            holiday_date += datetime.timedelta(days=1)

        Holiday.objects.create(
            holiday_date=holiday_date,
            title='Monsoon Heavy Rain Warning',
            description='Canopy operations closed due to winds'
        )

        is_valid, msg, holiday = validate_booking_date(holiday_date)
        self.assertFalse(is_valid)
        self.assertIn("Sorry! Bookings are not available on this date", msg)
        self.assertIsNotNone(holiday)

        # AJAX returns is_holiday=True
        res = self.client.get(f"{reverse('bookings:api_availability')}?date={holiday_date.strftime('%Y-%m-%d')}")
        data = res.json()
        self.assertFalse(data['success'])
        self.assertTrue(data['is_holiday'])

        # Atomic create raises ValidationError
        with self.assertRaises(ValidationError):
            create_booking_atomic(
                full_name='Test Rider',
                mobile_number='9876543210',
                email='rider@example.com',
                place='Bangalore',
                booking_date=holiday_date,
                slot_id=self.slot1.id,
                number_of_members=2
            )

    def test_07_available_slots_are_displayed(self):
        """Scenario 7: Available slots are displayed."""
        result = get_available_slots_for_date(self.valid_date)
        self.assertTrue(result['success'])
        self.assertEqual(len(result['slots']), 4)
        for s in result['slots']:
            self.assertEqual(s['available_seats'], 6)

    def test_08_fully_booked_slots_are_hidden(self):
        """Scenario 8: Fully booked slots are hidden from customers."""
        # Book all 6 seats in slot 1
        create_booking_atomic(
            full_name='Full Group',
            mobile_number='9876543210',
            email='full@example.com',
            place='Cochin',
            booking_date=self.valid_date,
            slot_id=self.slot1.id,
            number_of_members=6
        )

        result = get_available_slots_for_date(self.valid_date)
        self.assertTrue(result['success'])
        slot_ids = [s['id'] for s in result['slots']]
        # Slot 1 has 0 seats left and MUST NOT be in the returned available slots!
        self.assertNotIn(self.slot1.id, slot_ids)
        self.assertEqual(len(result['slots']), 3)

    def test_09_booking_for_one_member_works(self):
        """Scenario 9: Booking for one member works."""
        booking = create_booking_atomic(
            full_name='Solo Flyer',
            mobile_number='9876543210',
            email='solo@example.com',
            place='Bangalore',
            booking_date=self.valid_date,
            slot_id=self.slot1.id,
            number_of_members=1
        )
        self.assertIsNotNone(booking.id)
        self.assertTrue(booking.booking_reference.startswith('BEZ-'))
        self.assertEqual(booking.number_of_members, 1)
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

        # Slot 1 now has 5 seats left
        result = get_available_slots_for_date(self.valid_date)
        slot1_data = next(s for s in result['slots'] if s['id'] == self.slot1.id)
        self.assertEqual(slot1_data['available_seats'], 5)

    def test_10_booking_for_six_members_works_when_capacity_available(self):
        """Scenario 10: Booking for six members works when capacity is available."""
        booking = create_booking_atomic(
            full_name='Full Six Group',
            mobile_number='9876543210',
            email='six@example.com',
            place='Chennai',
            booking_date=self.valid_date,
            slot_id=self.slot2.id,
            number_of_members=6
        )
        self.assertEqual(booking.number_of_members, 6)
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

    def test_11_booking_for_more_than_six_members_is_rejected(self):
        """Scenario 11: Booking for more than six members is rejected."""
        with self.assertRaises(ValidationError):
            create_booking_atomic(
                full_name='Too Many',
                mobile_number='9876543210',
                email='toomany@example.com',
                place='Mumbai',
                booking_date=self.valid_date,
                slot_id=self.slot1.id,
                number_of_members=7
            )

    def test_12_insufficient_remaining_capacity_is_rejected(self):
        """Scenario 12: Insufficient remaining capacity is rejected."""
        # Book 4 members first
        create_booking_atomic(
            full_name='First Four',
            mobile_number='9876543210',
            email='first@example.com',
            place='Pune',
            booking_date=self.valid_date,
            slot_id=self.slot1.id,
            number_of_members=4
        )

        # Slot 1 only has 2 seats left. Trying to book 3 seats should be rejected!
        with self.assertRaises(ValidationError) as ctx:
            create_booking_atomic(
                full_name='Second Three',
                mobile_number='9876543211',
                email='second@example.com',
                place='Pune',
                booking_date=self.valid_date,
                slot_id=self.slot1.id,
                number_of_members=3
            )
        self.assertIn("exceed remaining available capacity", str(ctx.exception))

    def test_13_cancelled_booking_releases_seats(self):
        """Scenario 13: Cancelled booking releases seats."""
        booking = create_booking_atomic(
            full_name='Cancel Candidate',
            mobile_number='9876543210',
            email='cancel@example.com',
            place='Hyderabad',
            booking_date=self.valid_date,
            slot_id=self.slot3.id,
            number_of_members=4
        )

        # Before cancellation: 2 seats left
        res1 = get_available_slots_for_date(self.valid_date)
        s3_data = next(s for s in res1['slots'] if s['id'] == self.slot3.id)
        self.assertEqual(s3_data['available_seats'], 2)

        # Cancel the booking
        cancel_booking_atomic(booking, reason="Customer cancelled")
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CANCELLED)

        # After cancellation: all 6 seats released back!
        res2 = get_available_slots_for_date(self.valid_date)
        s3_data_after = next(s for s in res2['slots'] if s['id'] == self.slot3.id)
        self.assertEqual(s3_data_after['available_seats'], 6)

    def test_14_modified_booking_updates_availability(self):
        """Scenario 14: Modified booking updates availability."""
        booking = create_booking_atomic(
            full_name='Reschedule Candidate',
            mobile_number='9876543210',
            email='mod@example.com',
            place='Goa',
            booking_date=self.valid_date,
            slot_id=self.slot1.id,
            number_of_members=4
        )

        # Move from slot 1 to slot 2, changing members from 4 to 3
        modify_booking_atomic(
            booking=booking,
            new_date=self.valid_date,
            new_slot_id=self.slot2.id,
            new_members=3,
            notes="Customer rescheduled to midday"
        )

        res = get_available_slots_for_date(self.valid_date)
        # Slot 1 should now have full 6 seats available
        s1 = next(s for s in res['slots'] if s['id'] == self.slot1.id)
        self.assertEqual(s1['available_seats'], 6)

        # Slot 2 should have 6 - 3 = 3 seats available
        s2 = next(s for s in res['slots'] if s['id'] == self.slot2.id)
        self.assertEqual(s2['available_seats'], 3)

    def test_15_booking_lookup_portal(self):
        """Scenario 15: Self-service booking lookup and boarding pass retrieval."""
        # 1. Lookup page loads
        response = self.client.get(reverse('bookings:booking_lookup'))
        self.assertEqual(response.status_code, 200)

        # Create a booking
        booking = create_booking_atomic(
            full_name='Test Lookup Rider',
            mobile_number='9876543210',
            email='lookup@example.com',
            place='Kochi',
            booking_date=self.valid_date,
            slot_id=self.slot1.id,
            number_of_members=2
        )

        # 2. Lookup by reference via GET ?ref=
        response = self.client.get(reverse('bookings:booking_lookup') + f'?ref={booking.booking_reference}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, booking.booking_reference)
        self.assertContains(response, 'Test Lookup Rider')

        # 3. Lookup by POST
        response = self.client.post(reverse('bookings:booking_lookup'), {
            'booking_reference': booking.booking_reference,
            'mobile_number': '9876543210'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, booking.booking_reference)

        # 4. Lookup by mobile number alone (reference is optional)
        response = self.client.post(reverse('bookings:booking_lookup'), {
            'mobile_number': '9876543210'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, booking.booking_reference)
        self.assertContains(response, 'Test Lookup Rider')

        # 5. Lookup with invalid reference
        response = self.client.post(reverse('bookings:booking_lookup'), {
            'booking_reference': 'BEZ-INVALID-999999'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No reservation found matching reference')

        # 6. Lookup with empty inputs
        response = self.client.post(reverse('bookings:booking_lookup'), {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter your Booking Reference or your Registered Mobile Number')


class ConcurrencyBookingTests(TransactionTestCase):
    """
    Scenario 21: Concurrent booking attempts cannot exceed capacity.
    Using TransactionTestCase to test real database transaction isolation and locks.
    """
    def setUp(self):
        self.slot = BookingSlot.objects.create(
            name='Concurrent Slot',
            start_time=datetime.time(10, 0),
            end_time=datetime.time(12, 0),
            max_capacity=6,
            is_active=True,
            order=1
        )
        today = timezone.localdate()
        self.valid_date = today + datetime.timedelta(days=3)
        if self.valid_date.weekday() == 2:
            self.valid_date += datetime.timedelta(days=1)

    def test_21_concurrent_booking_attempts_cannot_exceed_capacity(self):
        """
        Scenario 21: Simulates 3 simultaneous booking attempts for 3 members each
        on a slot with capacity 6. Total requested = 9. Exactly 2 must succeed (6 pax)
        and 1 must fail with ValidationError!
        """
        successes = []
        failures = []

        import time
        from django.db import OperationalError

        def attempt_booking(idx):
            for attempt in range(10):
                try:
                    booking = create_booking_atomic(
                        full_name=f'Concurrent Rider {idx}',
                        mobile_number=f'987654321{idx}',
                        email=f'rider{idx}@example.com',
                        place='Bangalore',
                        booking_date=self.valid_date,
                        slot_id=self.slot.id,
                        number_of_members=3
                    )
                    successes.append(booking.id)
                    break
                except ValidationError as e:
                    failures.append(str(e))
                    break
                except OperationalError:
                    time.sleep(0.05)
                except Exception as e:
                    failures.append(str(e))
                    break

        threads = [threading.Thread(target=attempt_booking, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Invariant 1: Total confirmed members in DB must NEVER exceed capacity (6)
        confirmed_pax = Booking.objects.filter(
            booking_date=self.valid_date,
            slot=self.slot,
            status=Booking.Status.CONFIRMED
        ).aggregate(total=models.Sum('number_of_members'))['total'] or 0
        self.assertEqual(confirmed_pax, 6)

        # Invariant 2: Exactly 2 bookings succeeded and 1 was prevented
        self.assertEqual(len(successes), 2)
        self.assertEqual(len(failures), 1)
        self.assertIn("exceed remaining available capacity", failures[0])
