from django.urls import path
from apps.dashboard import views

app_name = 'dashboard'

urlpatterns = [
    path('admin-panel/login/', views.admin_login_view, name='login'),
    path('admin-panel/logout/', views.admin_logout_view, name='logout'),
    path('admin-panel/dashboard/', views.dashboard_index, name='index'),
    path('admin-panel/bookings/', views.bookings_list, name='bookings_list'),
    path('admin-panel/bookings/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('admin-panel/slots/', views.slots_list, name='slots_list'),
    path('admin-panel/slots/save/', views.slot_save, name='slot_create'),
    path('admin-panel/slots/<int:slot_id>/save/', views.slot_save, name='slot_edit'),
    path('admin-panel/slots/<int:slot_id>/toggle/', views.slot_toggle, name='slot_toggle'),
    path('admin-panel/holidays/', views.holidays_list, name='holidays_list'),
    path('admin-panel/website-settings/', views.website_settings_edit, name='settings_edit'),
    path('admin-panel/gallery/', views.gallery_manage, name='gallery_manage'),
    path('admin-panel/pricing/', views.pricing_manage, name='pricing_manage'),
    path('admin-panel/safety/', views.safety_manage, name='safety_manage'),
]

