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
from apps.core.utils import extract_validation_error_message


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
    return render(request, 'bookings/booking_success.html', {
        'booking': booking,
        'site_settings': site_settings,
    })

