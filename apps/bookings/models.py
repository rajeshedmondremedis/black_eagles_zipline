from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class BookingSlot(models.Model):
    """
    Configurable daily operating slot. Initially 4 slots configured by default.
    Capacity defaults to 6 members.
    """
    name = models.CharField(max_length=100, help_text="e.g. Slot 1 (Morning Flight)")
    start_time = models.TimeField()
    end_time = models.TimeField()
    max_capacity = models.PositiveIntegerField(
        default=6,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        help_text="Maximum allowed confirmed riders in this slot per operating day"
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'start_time']
        verbose_name = "Booking Slot"
        verbose_name_plural = "Booking Slots"

    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')})"

    @property
    def formatted_time(self):
        return f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"


class Holiday(models.Model):
    """
    Administrator defined holidays and blackout dates when zipline operations are suspended.
    Note: Wednesday is automatically blocked by business logic regardless of this table.
    """
    holiday_date = models.DateField(unique=True, db_index=True)
    title = models.CharField(max_length=150, help_text="e.g. National Holiday, Monsoon Severe Weather")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['holiday_date']
        verbose_name = "Holiday"
        verbose_name_plural = "Holidays"

    def __str__(self):
        return f"{self.holiday_date.strftime('%d %b %Y')} - {self.title}"


class Booking(models.Model):
    """
    Confirmed customer zipline reservations.
    """
    class Status(models.TextChoices):
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    booking_reference = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        help_text="Unique booking identifier e.g. BEZ-2026-000001"
    )
    full_name = models.CharField(max_length=120)
    mobile_number = models.CharField(max_length=20)
    email = models.EmailField()
    place = models.CharField(max_length=100, help_text="City or Place of origin")
    booking_date = models.DateField(db_index=True)
    slot = models.ForeignKey(
        BookingSlot,
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    number_of_members = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        help_text="Number of riders (1 - 6 allowed per booking)"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
        db_index=True
    )
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-booking_date', '-created_at']
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        indexes = [
            models.Index(fields=['booking_date', 'slot', 'status']),
            models.Index(fields=['booking_reference']),
            models.Index(fields=['mobile_number']),
        ]

    def __str__(self):
        return f"[{self.booking_reference}] {self.full_name} ({self.number_of_members} pax on {self.booking_date})"


class BookingAuditLog(models.Model):
    """
    Audit log tracking all booking lifecycle actions (creation, modification, cancellation).
    """
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=50)  # CREATED, MODIFIED, CANCELLED
    performed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Admin user who made change, or None if customer online booking"
    )
    details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Booking Audit Log"
        verbose_name_plural = "Booking Audit Logs"

    def __str__(self):
        return f"{self.action} on {self.booking.booking_reference} at {self.timestamp}"
