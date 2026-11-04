import datetime
import logging
from django.db import transaction, models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from apps.bookings.models import Booking, BookingSlot, Holiday, BookingAuditLog
from apps.core.models import SiteSettings

logger = logging.getLogger(__name__)


def validate_booking_date(date_val):
    """
    Validates whether operations are available on a given date.
    Returns (is_valid, error_message, holiday_obj).
    """
    if isinstance(date_val, str):
        try:
            date_val = datetime.date.fromisoformat(date_val)
        except ValueError:
            return False, "Invalid date format. Use YYYY-MM-DD.", None

    today = timezone.localdate()
    if date_val < today:
        return False, "Past dates cannot be selected for zipline bookings.", None

    # Wednesday is day 2 (Monday is 0, Tuesday is 1, Wednesday is 2)
    if date_val.weekday() == 2:
        return False, "Sorry! Bookings are not available on this date.", None

    # Check holiday table
    holiday = Holiday.objects.filter(holiday_date=date_val).first()
    if holiday:
        return False, "Sorry! Bookings are not available on this date.", holiday

    return True, "", None


def get_available_slots_for_date(date_val):
    """
    Returns available active slots for the customer on the specified date.
    Slots with 0 remaining capacity are excluded from the list.
    """
    is_valid, error_msg, _ = validate_booking_date(date_val)
    if not is_valid:
        return {
            'success': False,
            'is_holiday': True,
            'message': error_msg,
            'slots': []
        }

    active_slots = BookingSlot.objects.filter(is_active=True).order_by('order', 'start_time')
    available_slots = []

    for slot in active_slots:
        booked_members = Booking.objects.filter(
            booking_date=date_val,
            slot=slot,
            status=Booking.Status.CONFIRMED
        ).aggregate(total=models.Sum('number_of_members'))['total'] or 0

        remaining_capacity = max(0, slot.max_capacity - booked_members)

        # Prompt Requirement 5.4: "Fully booked slots must not be displayed. Hide the slot from customers."
        if remaining_capacity > 0:
            available_slots.append({
                'id': slot.id,
                'name': slot.name,
                'start_time': slot.start_time.strftime('%I:%M %p'),
                'end_time': slot.end_time.strftime('%I:%M %p'),
                'formatted_time': slot.formatted_time,
                'max_capacity': slot.max_capacity,
                'booked_members': booked_members,
                'available_seats': remaining_capacity,
            })

    return {
        'success': True,
        'is_holiday': False,
        'message': 'Slots retrieved successfully.' if available_slots else 'All slots are fully booked for this date.',
        'slots': available_slots
    }


def generate_booking_reference():
    """
    Generates a unique booking reference in the format BEZ-YYYY-XXXXXX
    e.g. BEZ-2026-000001
    """
    year = timezone.now().year
    prefix = f"BEZ-{year}-"
    
    # Find highest reference in current year
    last_booking = Booking.objects.filter(booking_reference__startswith=prefix).order_by('-booking_reference').first()
    if last_booking:
        try:
            seq_part = last_booking.booking_reference.replace(prefix, '')
            next_seq = int(seq_part) + 1
        except ValueError:
            next_seq = Booking.objects.count() + 1
    else:
        next_seq = 1

    reference = f"{prefix}{next_seq:06d}"
    # Safety check against collisions
    while Booking.objects.filter(booking_reference=reference).exists():
        next_seq += 1
        reference = f"{prefix}{next_seq:06d}"
    return reference


def create_booking_atomic(
    full_name,
    mobile_number,
    email,
    place,
    booking_date,
    slot_id,
    number_of_members,
    admin_notes="",
    created_by_user=None
):
    """
    Database-level concurrent booking creation using transaction.atomic()
    and select_for_update() to prevent double-booking of remaining capacity.
    """
    # 1. Validate Date
    is_valid, error_msg, _ = validate_booking_date(booking_date)
    if not is_valid:
        raise ValidationError(error_msg)

    # 2. Validate member count
    if not (1 <= int(number_of_members) <= 6):
        raise ValidationError("Number of members must be between 1 and 6.")

    # 3. Database transaction with row lock
    with transaction.atomic():
        try:
            # Lock the slot record to serialize slot calculations
            slot = BookingSlot.objects.select_for_update().get(id=slot_id, is_active=True)
        except BookingSlot.DoesNotExist:
            raise ValidationError("The selected booking slot does not exist or is inactive.")

        # Recalculate confirmed booked members under database lock
        # Note: on SQLite select_for_update() is a no-op but transaction.atomic() locks the file;
        # on MySQL 8.x select_for_update() applies real row-level exclusive locks.
        confirmed_count = Booking.objects.select_for_update().filter(
            booking_date=booking_date,
            slot=slot,
            status=Booking.Status.CONFIRMED
        ).aggregate(total=models.Sum('number_of_members'))['total'] or 0

        remaining_capacity = slot.max_capacity - confirmed_count

        if int(number_of_members) > remaining_capacity:
            raise ValidationError(
                f"Requested seats ({number_of_members}) exceed remaining available capacity ({remaining_capacity}) for this slot."
            )

        reference = generate_booking_reference()

        booking = Booking.objects.create(
            booking_reference=reference,
            full_name=full_name.strip(),
            mobile_number=mobile_number.strip(),
            email=email.strip().lower(),
            place=place.strip(),
            booking_date=booking_date,
            slot=slot,
            number_of_members=int(number_of_members),
            status=Booking.Status.CONFIRMED,
            admin_notes=admin_notes
        )

        BookingAuditLog.objects.create(
            booking=booking,
            action='CREATED',
            performed_by=created_by_user,
            details=f"Booking confirmed for {number_of_members} pax on {booking_date} ({slot.formatted_time}). Remaining capacity was {remaining_capacity - int(number_of_members)}."
        )

    # 4. Trigger email notification (asynchronous / fail-safe)
    try:
        send_booking_confirmation_email(booking)
    except Exception as e:
        logger.warning(f"Could not dispatch confirmation email for {booking.booking_reference}: {e}")

    return booking


def cancel_booking_atomic(booking, admin_user=None, reason="Cancelled by customer or administrator."):
    """
    Cancels a confirmed booking, immediately releasing its capacity back to the slot pool.
    """
    with transaction.atomic():
        booking = Booking.objects.select_for_update().get(id=booking.id)
        if booking.status == Booking.Status.CANCELLED:
            return booking

        booking.status = Booking.Status.CANCELLED
        booking.save()

        BookingAuditLog.objects.create(
            booking=booking,
            action='CANCELLED',
            performed_by=admin_user,
            details=f"Booking cancelled. Reason: {reason}. Released {booking.number_of_members} seat(s)."
        )
    return booking


def modify_booking_atomic(booking, new_date, new_slot_id, new_members, admin_user=None, notes=""):
    """
    Safely modifies an existing booking with strict capacity re-validation.
    """
    is_valid, error_msg, _ = validate_booking_date(new_date)
    if not is_valid:
        raise ValidationError(error_msg)

    if not (1 <= int(new_members) <= 6):
        raise ValidationError("Number of members must be between 1 and 6.")

    with transaction.atomic():
        booking = Booking.objects.select_for_update().get(id=booking.id)
        new_slot = BookingSlot.objects.select_for_update().get(id=new_slot_id, is_active=True)

        # Calculate booked count excluding this current booking
        booked_query = Booking.objects.select_for_update().filter(
            booking_date=new_date,
            slot=new_slot,
            status=Booking.Status.CONFIRMED
        ).exclude(id=booking.id)

        current_booked = booked_query.aggregate(total=models.Sum('number_of_members'))['total'] or 0
        remaining_capacity = new_slot.max_capacity - current_booked

        if int(new_members) > remaining_capacity:
            raise ValidationError(
                f"Cannot modify: only {remaining_capacity} seat(s) available on {new_date} for {new_slot.formatted_time}."
            )

        old_desc = f"{booking.booking_date} ({booking.slot.name}), {booking.number_of_members} pax"
        
        booking.booking_date = new_date
        booking.slot = new_slot
        booking.number_of_members = int(new_members)
        booking.status = Booking.Status.CONFIRMED
        if notes:
            booking.admin_notes = f"{booking.admin_notes}\n{notes}".strip()
        booking.save()

        BookingAuditLog.objects.create(
            booking=booking,
            action='MODIFIED',
            performed_by=admin_user,
            details=f"Booking rescheduled from {old_desc} to {new_date} ({new_slot.formatted_time}), {new_members} pax. Notes: {notes}"
        )

    return booking


def send_booking_confirmation_email(booking):
    """
    Renders and sends an email confirmation. Uses configured SMTP or falls back
    to Django console backend smoothly.
    """
    site_settings = SiteSettings.get_settings()
    subject = f"Booking Confirmation - {booking.booking_reference} | {site_settings.site_name}"
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@blackeagleszipline.com')
    recipient_list = [booking.email]

    context = {
        'booking': booking,
        'site_settings': site_settings,
    }

    message_txt = (
        f"Dear {booking.full_name},\n\n"
        f"Your reservation with Black Eagles Zipline is CONFIRMED!\n\n"
        f"Booking Reference: {booking.booking_reference}\n"
        f"Date: {booking.booking_date.strftime('%A, %d %B %Y')}\n"
        f"Time Slot: {booking.slot.formatted_time} ({booking.slot.name})\n"
        f"Riders: {booking.number_of_members} Person(s)\n"
        f"Place of origin: {booking.place}\n\n"
        f"Location: {site_settings.address}\n"
        f"Contact Helpline: {site_settings.phone_number}\n\n"
        f"Important Guidelines:\n"
        f"1. Please arrive at least 20 minutes prior to your time slot for gear fitting and mandatory safety briefing.\n"
        f"2. Closed-toe athletic or hiking footwear is strictly required.\n"
        f"3. Follow all certified jumpmaster instructions on platform towers.\n\n"
        f"Fly Beyond Limits!\n"
        f"Black Eagles Zipline Team"
    )

    try:
        send_mail(
            subject=subject,
            message=message_txt,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=True
        )
    except Exception as e:
        logger.error(f"Failed to send confirmation email: {e}")

