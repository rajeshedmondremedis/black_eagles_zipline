import datetime
from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.bookings.models import Booking, BookingSlot
from apps.bookings.services import validate_booking_date


class CustomerBookingForm(forms.Form):
    full_name = forms.CharField(
        max_length=120,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Full Name',
            'required': 'required'
        })
    )
    mobile_number = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '10-digit Mobile Number',
            'type': 'tel',
            'required': 'required'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Email Address for confirmation',
            'required': 'required'
        })
    )
    place = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'City / Hometown',
            'required': 'required'
        })
    )
    booking_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-lg datepicker-input',
            'type': 'date',
            'required': 'required'
        })
    )
    slot_id = forms.IntegerField(
        required=True,
        widget=forms.HiddenInput()
    )
    number_of_members = forms.IntegerField(
        min_value=1,
        max_value=6,
        initial=1,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg text-center fw-bold',
            'min': '1',
            'max': '6',
            'value': '1',
            'required': 'required'
        })
    )

    def clean_booking_date(self):
        booking_date = self.cleaned_data.get('booking_date')
        if not booking_date:
            raise forms.ValidationError("Please choose a valid booking date.")
        is_valid, error_msg, _ = validate_booking_date(booking_date)
        if not is_valid:
            raise forms.ValidationError(error_msg)
        return booking_date

    def clean_mobile_number(self):
        mobile = self.cleaned_data.get('mobile_number', '').strip()
        # Ensure it contains at least 7 digits
        digits = [c for c in mobile if c.isdigit()]
        if len(digits) < 7:
            raise forms.ValidationError("Please provide a valid phone number with at least 7 digits.")
        return mobile

    def clean(self):
        cleaned_data = super().clean()
        slot_id = cleaned_data.get('slot_id')
        if slot_id:
            try:
                slot = BookingSlot.objects.get(id=slot_id, is_active=True)
                cleaned_data['slot'] = slot
            except BookingSlot.DoesNotExist:
                self.add_error('slot_id', "Selected slot is invalid or inactive.")
        return cleaned_data


class AdminBookingEditForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['full_name', 'mobile_number', 'email', 'place', 'booking_date', 'slot', 'number_of_members', 'status', 'admin_notes']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'place': forms.TextInput(attrs={'class': 'form-control'}),
            'booking_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'slot': forms.Select(attrs={'class': 'form-select'}),
            'number_of_members': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 6}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'admin_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
