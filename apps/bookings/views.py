import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.utils import timezone
import datetime

from apps.bookings.models import Booking, BookingSlot
from apps.bookings.forms import CustomerBookingForm
from apps.bookings.services import (
    get_available_slots_for_date,
    create_booking_atomic,
    validate_booking_date
)
from apps.core.models import SiteSettings
from apps.core.utils import extract_validation_error_message, generate_qr_svg


def booking_page(request):
    """
    Renders the main customer booking interface.
    Pre-populates tomorrow or nearest valid operating date as default.
    """
    today = timezone.localdate()
    # Default to tomorrow, skipping Wednesday if tomorrow is Wednesday
    target_date = today + datetime.timedelta(days=1)
    if target_date.weekday() == 2:  # Wednesday
        target_date += datetime.timedelta(days=1)

    min_date = today.strftime('%Y-%m-%d')
    # Can book up to 90 days in advance
    max_date = (today + datetime.timedelta(days=90)).strftime('%Y-%m-%d')
    default_date = target_date.strftime('%Y-%m-%d')

    form = CustomerBookingForm(initial={
        'booking_date': default_date,
        'number_of_members': 1
    })

    return render(request, 'bookings/booking_page.html', {
        'form': form,
        'min_date': min_date,
        'max_date': max_date,
        'default_date': default_date,
        'today': today,
    })


def api_slot_availability(request):
    """
    AJAX endpoint to retrieve real-time slot availability for a chosen date.
    Returns JSON containing remaining seats and whether the date is a holiday/Wednesday.
    """
    date_str = request.GET.get('date', '').strip()
    if not date_str:
        return JsonResponse({
            'success': False,
            'is_holiday': False,
            'message': 'Date parameter is required.',
            'slots': []
        }, status=400)

    try:
        booking_date = datetime.date.fromisoformat(date_str)
    except ValueError:
        return JsonResponse({
            'success': False,
            'is_holiday': False,
            'message': 'Invalid date format. Expected YYYY-MM-DD.',
            'slots': []
        }, status=400)

    result = get_available_slots_for_date(booking_date)
    return JsonResponse(result)


@require_http_methods(["POST"])
def booking_submit(request):
    """
    Validates submitted customer booking information and securely reserves
    slots under database-level concurrency protection.
    """
    form = CustomerBookingForm(request.POST)

    if form.is_valid():
        cd = form.cleaned_data
        try:
            booking = create_booking_atomic(
                full_name=cd['full_name'],
                mobile_number=cd['mobile_number'],
                email=cd['email'],
                place=cd['place'],
                booking_date=cd['booking_date'],
                slot_id=cd['slot_id'],
                number_of_members=cd['number_of_members']
            )
            return redirect('bookings:booking_success', reference=booking.booking_reference)
        except ValidationError as e:
            error_msg = extract_validation_error_message(e)
            messages.error(request, error_msg)
            return render(request, 'bookings/booking_page.html', {
                'form': form,
                'min_date': timezone.localdate().strftime('%Y-%m-%d'),
                'max_date': (timezone.localdate() + datetime.timedelta(days=90)).strftime('%Y-%m-%d'),
                'default_date': cd.get('booking_date', timezone.localdate()).strftime('%Y-%m-%d'),
                'error_message': error_msg
            }, status=400)
    else:
        # Collect first form error
        error_msg = "Please check the form for errors."
        for field, errors in form.errors.items():
            error_msg = f"{field.replace('_', ' ').capitalize()}: {errors[0]}"
            break
        messages.error(request, error_msg)
        return render(request, 'bookings/booking_page.html', {
            'form': form,
            'min_date': timezone.localdate().strftime('%Y-%m-%d'),
            'max_date': (timezone.localdate() + datetime.timedelta(days=90)).strftime('%Y-%m-%d'),
            'default_date': request.POST.get('booking_date', timezone.localdate().strftime('%Y-%m-%d')),
            'error_message': error_msg
        }, status=400)


def booking_success(request, reference):
    """
    Displays the confirmed booking confirmation with reference code,
    printable pass, and comprehensive business contact details.
    """
    booking = get_object_or_404(Booking, booking_reference=reference)
    site_settings = SiteSettings.get_settings()
    lookup_url = request.build_absolute_uri(f"/booking/lookup/?ref={booking.booking_reference}")
    qr_svg = generate_qr_svg(lookup_url, size=115)
    return render(request, 'bookings/booking_success.html', {
        'booking': booking,
        'site_settings': site_settings,
        'qr_svg': qr_svg,
    })


def booking_lookup(request):
    """
    Public self-service lookup portal allowing customers to retrieve their
    boarding pass voucher, check flight status, or reprint tickets using either
    their Booking Reference or their Registered Mobile Number.
    """
    site_settings = SiteSettings.get_settings()
    found_booking = None
    multiple_bookings = []
    search_attempted = False
    error_message = None

    ref_query = request.GET.get('ref', '').strip()
    mobile_query = request.GET.get('mobile', '').strip()

    if request.method == 'POST':
        ref_query = request.POST.get('booking_reference', '').strip()
        mobile_query = request.POST.get('mobile_number', '').strip()

    if ref_query or mobile_query:
        search_attempted = True
        qs = Booking.objects.select_related('slot')

        if ref_query and mobile_query:
            clean_mobile = ''.join(c for c in mobile_query if c.isdigit())
            match_ref = qs.filter(booking_reference__iexact=ref_query).first()
            if match_ref:
                clean_booking_mobile = ''.join(c for c in match_ref.mobile_number if c.isdigit())
                if clean_mobile and not clean_booking_mobile.endswith(clean_mobile[-10:]):
                    error_message = f"Reservation '{ref_query}' was found, but the registered mobile number does not match."
                else:
                    found_booking = match_ref
            else:
                error_message = f"No reservation found matching reference '{ref_query}'."

        elif ref_query:
            found_booking = qs.filter(booking_reference__iexact=ref_query).first()
            if not found_booking:
                error_message = f"No reservation found matching reference '{ref_query}'. Please verify your code."

        elif mobile_query:
            clean_mobile = ''.join(c for c in mobile_query if c.isdigit())
            if len(clean_mobile) >= 4:
                matches = list(qs.filter(mobile_number__icontains=clean_mobile[-10:]).order_by('-booking_date', '-created_at')[:10])
                if len(matches) == 1:
                    found_booking = matches[0]
                elif len(matches) > 1:
                    multiple_bookings = matches
                else:
                    error_message = f"No reservations found registered to mobile number '{mobile_query}'."
            else:
                error_message = "Please enter at least 4 digits of your registered mobile number."

    elif request.method == 'POST':
        search_attempted = True
        error_message = "Please enter your Booking Reference or your Registered Mobile Number to find your ticket."

    # Calculate flight countdown if a single booking is found
    days_until_flight = None
    is_today = False
    is_past = False
    qr_svg = None

    if found_booking:
        today = timezone.localdate()
        delta = (found_booking.booking_date - today).days
        days_until_flight = delta
        if delta == 0:
            is_today = True
        elif delta < 0:
            is_past = True

        lookup_url = request.build_absolute_uri(f"/booking/lookup/?ref={found_booking.booking_reference}")
        qr_svg = generate_qr_svg(lookup_url, size=115)

    return render(request, 'bookings/booking_lookup.html', {
        'site_settings': site_settings,
        'booking': found_booking,
        'multiple_bookings': multiple_bookings,
        'search_attempted': search_attempted,
        'error_message': error_message,
        'ref_query': ref_query,
        'mobile_query': mobile_query,
        'days_until_flight': days_until_flight,
        'is_today': is_today,
        'is_past': is_past,
        'qr_svg': qr_svg,
    })

