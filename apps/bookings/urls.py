from django.urls import path
from apps.bookings import views

app_name = 'bookings'

urlpatterns = [
    path('book/', views.booking_page, name='booking_page'),
    path('book/availability/', views.api_slot_availability, name='api_availability'),
    path('book/submit/', views.booking_submit, name='booking_submit'),
    path('booking/success/<str:reference>/', views.booking_success, name='booking_success'),
]

