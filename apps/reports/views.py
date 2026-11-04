import datetime
from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
from apps.core.decorators import admin_required
from apps.bookings.models import Booking, BookingSlot
from apps.reports.excel_generator import generate_bookings_excel
from apps.reports.pdf_generator import generate_bookings_pdf


def get_filtered_bookings(request):
    """
    Helper to extract filter parameters from request GET and filter Bookings.
    """
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    status = request.GET.get('status', '').strip()
    slot_id = request.GET.get('slot_id', '').strip()

    bookings = Booking.objects.select_related('slot').order_by('-booking_date', '-created_at')

    date_range_label = "All Dates"
    if start_date:
        try:
            s_date = datetime.date.fromisoformat(start_date)
            bookings = bookings.filter(booking_date__gte=s_date)
            date_range_label = f"From {start_date}"
        except ValueError:
            pass

    if end_date:
        try:
            e_date = datetime.date.fromisoformat(end_date)
            bookings = bookings.filter(booking_date__lte=e_date)
            if "From" in date_range_label:
                date_range_label += f" to {end_date}"
            else:
                date_range_label = f"Up to {end_date}"
        except ValueError:
            pass

    if status in ['CONFIRMED', 'CANCELLED']:
        bookings = bookings.filter(status=status)

    if slot_id and slot_id.isdigit():
        bookings = bookings.filter(slot_id=int(slot_id))

    filter_meta = {
        'date_range': date_range_label,
        'status': status or 'All',
        'start_date': start_date,
        'end_date': end_date,
        'slot_id': slot_id,
    }

    return bookings, filter_meta


@admin_required
def reports_page(request):
    bookings, filter_meta = get_filtered_bookings(request)
    slots = BookingSlot.objects.filter(is_active=True)

    total_count = bookings.count()
    confirmed_members = sum(b.number_of_members for b in bookings if b.status == 'CONFIRMED')

    return render(request, 'dashboard/reports.html', {
        'bookings': bookings[:100],  # preview 100
        'total_count': total_count,
        'confirmed_members': confirmed_members,
        'slots': slots,
        'filter_meta': filter_meta,
    })


@admin_required
def export_excel(request):
    bookings, filter_meta = get_filtered_bookings(request)
    excel_content = generate_bookings_excel(bookings, filter_meta)

    filename = f"Black_Eagles_Zipline_Bookings_{timezone.now().strftime('%Y%m%d_%H%M')}.xlsx"
    response = HttpResponse(
        excel_content,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@admin_required
def export_pdf(request):
    bookings, filter_meta = get_filtered_bookings(request)
    pdf_content = generate_bookings_pdf(bookings, filter_meta)

    filename = f"Black_Eagles_Zipline_Manifest_{timezone.now().strftime('%Y%m%d_%H%M')}.pdf"
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

