import os
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from PIL import Image

from apps.core.decorators import admin_required
from apps.core.utils import extract_validation_error_message
from apps.bookings.models import Booking, BookingSlot, Holiday, BookingAuditLog
from apps.bookings.services import (
    cancel_booking_atomic,
    modify_booking_atomic,
    validate_booking_date
)
from apps.core.models import SiteSettings
from apps.website.models import GalleryImage, SafetyGuideline, PricingPackage, ContactMessage

ALLOWED_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')
MAX_IMAGE_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def admin_login_view(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard:index')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_staff or user.is_superuser:
                login(request, user)
                next_url = request.GET.get('next') or 'dashboard:index'
                return redirect(next_url)
            else:
                messages.error(request, "Access denied. Administrative privileges required.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'dashboard/login.html')


def admin_logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('dashboard:login')


@admin_required
def dashboard_index(request):
    today = timezone.localdate()

    # Metrics
    total_bookings = Booking.objects.count()
    today_bookings = Booking.objects.filter(booking_date=today)
    today_confirmed_count = today_bookings.filter(status='CONFIRMED').count()
    upcoming_bookings = Booking.objects.filter(booking_date__gt=today, status='CONFIRMED').count()

    total_confirmed_members = Booking.objects.filter(status='CONFIRMED').aggregate(
        total=models.Sum('number_of_members')
    )['total'] or 0

    cancelled_bookings = Booking.objects.filter(status='CANCELLED').count()

    # Slot availability today
    active_slots = BookingSlot.objects.filter(is_active=True).order_by('order', 'start_time')
    slots_today_info = []
    available_slots_today_count = 0
    fully_booked_today_count = 0

    for slot in active_slots:
        booked_today = today_bookings.filter(slot=slot, status='CONFIRMED').aggregate(
            total=models.Sum('number_of_members')
        )['total'] or 0
        rem = max(0, slot.max_capacity - booked_today)
        if rem > 0:
            available_slots_today_count += 1
        else:
            fully_booked_today_count += 1

        occupancy_pct = int((booked_today / slot.max_capacity) * 100) if slot.max_capacity > 0 else 0
        slots_today_info.append({
            'slot': slot,
            'booked': booked_today,
            'remaining': rem,
            'occupancy_pct': min(occupancy_pct, 100),
            'is_full': rem == 0,
        })

    # Recent bookings
    recent_bookings = Booking.objects.select_related('slot').order_by('-created_at')[:8]

    # Weekly reservation trend (last 7 days)
    chart_dates = []
    chart_counts = []
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        day_str = day.strftime('%a (%d %b)')
        day_pax = Booking.objects.filter(booking_date=day, status='CONFIRMED').aggregate(
            total=models.Sum('number_of_members')
        )['total'] or 0
        chart_dates.append(day_str)
        chart_counts.append(day_pax)

    return render(request, 'dashboard/index.html', {
        'total_bookings': total_bookings,
        'today_confirmed_count': today_confirmed_count,
        'upcoming_bookings': upcoming_bookings,
        'total_confirmed_members': total_confirmed_members,
        'cancelled_bookings': cancelled_bookings,
        'available_slots_today_count': available_slots_today_count,
        'fully_booked_today_count': fully_booked_today_count,
        'slots_today_info': slots_today_info,
        'recent_bookings': recent_bookings,
        'chart_dates': chart_dates,
        'chart_counts': chart_counts,
        'today': today,
    })


@admin_required
def bookings_list(request):
    bookings = Booking.objects.select_related('slot').order_by('-booking_date', '-created_at')

    # Search
    q = request.GET.get('q', '').strip()
    if q:
        bookings = bookings.filter(
            models.Q(booking_reference__icontains=q) |
            models.Q(full_name__icontains=q) |
            models.Q(mobile_number__icontains=q) |
            models.Q(email__icontains=q) |
            models.Q(place__icontains=q)
        )

    # Filter Date
    booking_date = request.GET.get('date', '').strip()
    if booking_date:
        try:
            d = datetime.date.fromisoformat(booking_date)
            bookings = bookings.filter(booking_date=d)
        except ValueError:
            pass

    # Filter Slot
    slot_id = request.GET.get('slot', '').strip()
    if slot_id and slot_id.isdigit():
        bookings = bookings.filter(slot_id=int(slot_id))

    # Filter Status
    status = request.GET.get('status', '').strip()
    if status in ['CONFIRMED', 'CANCELLED']:
        bookings = bookings.filter(status=status)

    slots = BookingSlot.objects.filter(is_active=True)

    return render(request, 'dashboard/bookings_list.html', {
        'bookings': bookings,
        'slots': slots,
        'search_query': q,
        'selected_date': booking_date,
        'selected_slot': slot_id,
        'selected_status': status,
        'total_count': bookings.count(),
    })


@admin_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking.objects.select_related('slot'), id=booking_id)
    slots = BookingSlot.objects.filter(is_active=True)
    audit_logs = booking.audit_logs.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'cancel':
            reason = request.POST.get('cancel_reason', 'Cancelled via admin dashboard')
            cancel_booking_atomic(booking, admin_user=request.user, reason=reason)
            messages.success(request, f"Booking {booking.booking_reference} has been cancelled. Capacity released.")
            return redirect('dashboard:booking_detail', booking_id=booking.id)

        elif action == 'modify':
            new_date_str = request.POST.get('booking_date')
            new_slot_id = request.POST.get('slot')
            new_members = request.POST.get('number_of_members')
            notes = request.POST.get('admin_notes', '')

            try:
                new_date = datetime.date.fromisoformat(new_date_str)
                modify_booking_atomic(
                    booking=booking,
                    new_date=new_date,
                    new_slot_id=int(new_slot_id),
                    new_members=int(new_members),
                    admin_user=request.user,
                    notes=notes
                )
                messages.success(request, f"Booking {booking.booking_reference} updated successfully.")
                return redirect('dashboard:booking_detail', booking_id=booking.id)
            except ValidationError as e:
                messages.error(request, extract_validation_error_message(e))
            except Exception as e:
                messages.error(request, f"Failed to modify booking: {e}")

    return render(request, 'dashboard/booking_detail.html', {
        'booking': booking,
        'slots': slots,
        'audit_logs': audit_logs,
    })


@admin_required
def slots_list(request):
    slots = BookingSlot.objects.all().order_by('order', 'start_time')
    today = timezone.localdate()

    slot_stats = []
    for s in slots:
        today_confirmed = Booking.objects.filter(
            booking_date=today, slot=s, status='CONFIRMED'
        ).aggregate(total=models.Sum('number_of_members'))['total'] or 0

        slot_stats.append({
            'slot': s,
            'today_booked': today_confirmed,
            'today_remaining': max(0, s.max_capacity - today_confirmed),
        })

    return render(request, 'dashboard/slots_list.html', {
        'slot_stats': slot_stats,
        'today': today,
    })


@admin_required
def slot_save(request, slot_id=None):
    slot = get_object_or_404(BookingSlot, id=slot_id) if slot_id else None

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        start_time = request.POST.get('start_time', '').strip()
        end_time = request.POST.get('end_time', '').strip()
        max_capacity = request.POST.get('max_capacity', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        order = request.POST.get('order', '1').strip()

        try:
            capacity_int = int(max_capacity)
            if capacity_int < 1:
                raise ValueError("Capacity must be at least 1.")

            if slot:
                today = timezone.localdate()
                max_future_booking = Booking.objects.filter(
                    slot=slot,
                    booking_date__gte=today,
                    status='CONFIRMED'
                ).values('booking_date').annotate(
                    day_total=models.Sum('number_of_members')
                ).order_by('-day_total').first()

                if max_future_booking and max_future_booking['day_total'] > capacity_int:
                    messages.error(
                        request,
                        f"Unsafe operation! Cannot reduce capacity to {capacity_int}. An upcoming date ({max_future_booking['booking_date']}) already has {max_future_booking['day_total']} confirmed members."
                    )
                    return redirect('dashboard:slots_list')

                slot.name = name
                slot.start_time = start_time
                slot.end_time = end_time
                slot.max_capacity = capacity_int
                slot.is_active = is_active
                slot.order = int(order)
                slot.save()
                messages.success(request, f"Slot '{slot.name}' updated successfully.")
            else:
                BookingSlot.objects.create(
                    name=name,
                    start_time=start_time,
                    end_time=end_time,
                    max_capacity=capacity_int,
                    is_active=is_active,
                    order=int(order)
                )
                messages.success(request, f"New slot '{name}' created successfully.")

        except Exception as e:
            messages.error(request, f"Error saving slot: {e}")

    return redirect('dashboard:slots_list')


@admin_required
def slot_toggle(request, slot_id):
    slot = get_object_or_404(BookingSlot, id=slot_id)
    slot.is_active = not slot.is_active
    slot.save()
    status_str = "activated" if slot.is_active else "deactivated"
    messages.success(request, f"Slot '{slot.name}' has been {status_str}.")
    return redirect('dashboard:slots_list')


@admin_required
def holidays_list(request):
    holidays = Holiday.objects.all().order_by('holiday_date')
    today = timezone.localdate()

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            date_str = request.POST.get('holiday_date', '').strip()
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            override_warning = request.POST.get('override_warning') == '1'

            try:
                h_date = datetime.date.fromisoformat(date_str)
                
                if h_date.weekday() == 2:
                    messages.info(request, "Note: Wednesdays are already automatically blocked across the entire system.")

                existing_bookings = Booking.objects.filter(booking_date=h_date, status='CONFIRMED')
                if existing_bookings.exists() and not override_warning:
                    booked_pax = existing_bookings.aggregate(total=models.Sum('number_of_members'))['total'] or 0
                    messages.warning(
                        request,
                        f"WARNING: There are already {existing_bookings.count()} confirmed booking(s) ({booked_pax} total members) on {h_date.strftime('%d-%b-%Y')}. Please confirm you still want to designate this date as a holiday."
                    )
                    return render(request, 'dashboard/holidays_list.html', {
                        'holidays': holidays,
                        'today': today,
                        'pending_warning': True,
                        'warn_date': date_str,
                        'warn_title': title,
                        'warn_description': description,
                        'affected_count': existing_bookings.count(),
                        'affected_pax': booked_pax,
                    })

                Holiday.objects.create(
                    holiday_date=h_date,
                    title=title,
                    description=description
                )
                messages.success(request, f"Holiday on {h_date.strftime('%d %b %Y')} successfully scheduled.")
                return redirect('dashboard:holidays_list')
            except Exception as e:
                messages.error(request, f"Failed to add holiday: {e}")

        elif action == 'delete':
            h_id = request.POST.get('holiday_id')
            holiday = get_object_or_404(Holiday, id=h_id)
            holiday.delete()
            messages.success(request, "Holiday removed successfully.")
            return redirect('dashboard:holidays_list')

    return render(request, 'dashboard/holidays_list.html', {
        'holidays': holidays,
        'today': today,
    })


@admin_required
def website_settings_edit(request):
    settings_obj = SiteSettings.get_settings()

    if request.method == 'POST':
        settings_obj.site_name = request.POST.get('site_name', settings_obj.site_name).strip()
        settings_obj.tagline = request.POST.get('tagline', settings_obj.tagline).strip()
        settings_obj.hero_heading = request.POST.get('hero_heading', settings_obj.hero_heading).strip()
        settings_obj.hero_subheading = request.POST.get('hero_subheading', settings_obj.hero_subheading).strip()

        # Stats Ribbon Configuration
        settings_obj.stat_1_val = request.POST.get('stat_1_val', settings_obj.stat_1_val).strip()
        settings_obj.stat_1_lbl = request.POST.get('stat_1_lbl', settings_obj.stat_1_lbl).strip()
        settings_obj.stat_2_val = request.POST.get('stat_2_val', settings_obj.stat_2_val).strip()
        settings_obj.stat_2_lbl = request.POST.get('stat_2_lbl', settings_obj.stat_2_lbl).strip()
        settings_obj.stat_3_val = request.POST.get('stat_3_val', settings_obj.stat_3_val).strip()
        settings_obj.stat_3_lbl = request.POST.get('stat_3_lbl', settings_obj.stat_3_lbl).strip()
        settings_obj.stat_4_val = request.POST.get('stat_4_val', settings_obj.stat_4_val).strip()
        settings_obj.stat_4_lbl = request.POST.get('stat_4_lbl', settings_obj.stat_4_lbl).strip()

        settings_obj.phone_number = request.POST.get('phone_number', settings_obj.phone_number).strip()
        settings_obj.whatsapp_number = request.POST.get('whatsapp_number', settings_obj.whatsapp_number).strip()
        settings_obj.email_address = request.POST.get('email_address', settings_obj.email_address).strip()
        settings_obj.address = request.POST.get('address', settings_obj.address).strip()
        settings_obj.google_maps_embed_url = request.POST.get('google_maps_embed_url', settings_obj.google_maps_embed_url).strip()
        settings_obj.facebook_url = request.POST.get('facebook_url', settings_obj.facebook_url).strip()
        settings_obj.instagram_url = request.POST.get('instagram_url', settings_obj.instagram_url).strip()
        settings_obj.youtube_url = request.POST.get('youtube_url', settings_obj.youtube_url).strip()
        settings_obj.twitter_url = request.POST.get('twitter_url', settings_obj.twitter_url).strip()
        settings_obj.about_summary = request.POST.get('about_summary', settings_obj.about_summary).strip()
        settings_obj.about_story = request.POST.get('about_story', settings_obj.about_story).strip()
        settings_obj.safety_overview = request.POST.get('safety_overview', settings_obj.safety_overview).strip()
        settings_obj.operating_hours = request.POST.get('operating_hours', settings_obj.operating_hours).strip()

        settings_obj.save()
        messages.success(request, "Website settings and business information updated successfully.")
        return redirect('dashboard:settings_edit')

    return render(request, 'dashboard/website_settings.html', {
        'settings': settings_obj,
    })


@admin_required
def gallery_manage(request):
    images = GalleryImage.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            title = request.POST.get('title', '').strip()
            caption = request.POST.get('caption', '').strip()
            category = request.POST.get('category', 'zipline')
            is_featured = request.POST.get('is_featured') == 'on'
            image_file = request.FILES.get('image')

            if not (image_file and title):
                messages.error(request, "Please specify a title and choose an image file.")
                return redirect('dashboard:gallery_manage')

            # Security File Validation
            ext = os.path.splitext(image_file.name)[1].lower()
            if ext not in ALLOWED_IMAGE_EXTENSIONS:
                messages.error(request, f"Invalid file format '{ext}'. Allowed extensions: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}.")
                return redirect('dashboard:gallery_manage')

            if image_file.size > MAX_IMAGE_FILE_SIZE:
                messages.error(request, "File exceeds maximum upload size of 5 MB.")
                return redirect('dashboard:gallery_manage')

            try:
                # Verify genuine image structure using Pillow
                img = Image.open(image_file)
                img.verify()
                image_file.seek(0)
            except Exception:
                messages.error(request, "Invalid or corrupted image file.")
                return redirect('dashboard:gallery_manage')

            GalleryImage.objects.create(
                title=title,
                caption=caption,
                category=category,
                is_featured=is_featured,
                image=image_file
            )
            messages.success(request, "New photo added to the gallery.")
            return redirect('dashboard:gallery_manage')

        elif action == 'delete':
            img_id = request.POST.get('image_id')
            img = get_object_or_404(GalleryImage, id=img_id)
            img.delete()
            messages.success(request, "Gallery photo removed.")
            return redirect('dashboard:gallery_manage')

        elif action == 'toggle_featured':
            img_id = request.POST.get('image_id')
            img = get_object_or_404(GalleryImage, id=img_id)
            img.is_featured = not img.is_featured
            img.save()
            messages.success(request, f"Featured status updated for '{img.title}'.")
            return redirect('dashboard:gallery_manage')

    return render(request, 'dashboard/gallery_manage.html', {
        'images': images,
        'categories': GalleryImage.CATEGORY_CHOICES,
    })


@admin_required
def pricing_manage(request):
    packages = PricingPackage.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save':
            pkg_id = request.POST.get('package_id')
            name = request.POST.get('name', '').strip()
            badge = request.POST.get('badge', '').strip()
            price = request.POST.get('price', '').strip()
            duration = request.POST.get('duration', '').strip()
            description = request.POST.get('description', '').strip()
            features = request.POST.get('features', '').strip()
            is_featured = request.POST.get('is_featured') == 'on'
            is_active = request.POST.get('is_active') == 'on'
            order = request.POST.get('order', '0')

            if pkg_id:
                pkg = get_object_or_404(PricingPackage, id=pkg_id)
                pkg.name = name
                pkg.badge = badge
                pkg.price = price
                pkg.duration = duration
                pkg.description = description
                pkg.features = features
                pkg.is_featured = is_featured
                pkg.is_active = is_active
                pkg.order = int(order)
                pkg.save()
                messages.success(request, f"Package '{name}' updated.")
            else:
                PricingPackage.objects.create(
                    name=name,
                    badge=badge,
                    price=price,
                    duration=duration,
                    description=description,
                    features=features,
                    is_featured=is_featured,
                    is_active=is_active,
                    order=int(order)
                )
                messages.success(request, f"Package '{name}' created.")
            return redirect('dashboard:pricing_manage')

        elif action == 'delete':
            pkg_id = request.POST.get('package_id')
            pkg = get_object_or_404(PricingPackage, id=pkg_id)
            pkg.delete()
            messages.success(request, "Package deleted.")
            return redirect('dashboard:pricing_manage')

    return render(request, 'dashboard/pricing_manage.html', {
        'packages': packages,
    })


@admin_required
def safety_manage(request):
    guidelines = SafetyGuideline.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save':
            g_id = request.POST.get('guideline_id')
            category = request.POST.get('category', 'mandatory')
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            icon_name = request.POST.get('icon_name', 'shield-check').strip()
            is_active = request.POST.get('is_active') == 'on'
            order = request.POST.get('order', '0')

            if g_id:
                guide = get_object_or_404(SafetyGuideline, id=g_id)
                guide.category = category
                guide.title = title
                guide.description = description
                guide.icon_name = icon_name
                guide.is_active = is_active
                guide.order = int(order)
                guide.save()
                messages.success(request, f"Guideline '{title}' updated.")
            else:
                SafetyGuideline.objects.create(
                    category=category,
                    title=title,
                    description=description,
                    icon_name=icon_name,
                    is_active=is_active,
                    order=int(order)
                )
                messages.success(request, f"Guideline '{title}' created.")
            return redirect('dashboard:safety_manage')

        elif action == 'delete':
            g_id = request.POST.get('guideline_id')
            guide = get_object_or_404(SafetyGuideline, id=g_id)
            guide.delete()
            messages.success(request, "Guideline removed.")
            return redirect('dashboard:safety_manage')

    return render(request, 'dashboard/safety_manage.html', {
        'guidelines': guidelines,
        'categories': SafetyGuideline.CATEGORY_CHOICES,
    })
