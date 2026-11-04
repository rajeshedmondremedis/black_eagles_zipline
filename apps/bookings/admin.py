from django.contrib import admin
from apps.bookings.models import BookingSlot, Holiday, Booking, BookingAuditLog


@admin.register(BookingSlot)
class BookingSlotAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time', 'max_capacity', 'is_active', 'order')
    list_filter = ('is_active',)
    list_editable = ('max_capacity', 'is_active', 'order')


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('holiday_date', 'title', 'created_at')
    search_fields = ('title', 'description')


class BookingAuditLogInline(admin.TabularInline):
    model = BookingAuditLog
    extra = 0
    readonly_fields = ('action', 'performed_by', 'details', 'timestamp')
    can_delete = False


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'booking_reference', 'full_name', 'mobile_number',
        'booking_date', 'slot', 'number_of_members', 'status', 'created_at'
    )
    list_filter = ('status', 'booking_date', 'slot')
    search_fields = ('booking_reference', 'full_name', 'mobile_number', 'email', 'place')
    inlines = [BookingAuditLogInline]


@admin.register(BookingAuditLog)
class BookingAuditLogAdmin(admin.ModelAdmin):
    list_display = ('booking', 'action', 'performed_by', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('booking__booking_reference', 'details')
