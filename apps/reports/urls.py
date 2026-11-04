from django.urls import path
from apps.reports import views

app_name = 'reports'

urlpatterns = [
    path('admin-panel/reports/', views.reports_page, name='reports_page'),
    path('admin-panel/reports/excel/', views.export_excel, name='export_excel'),
    path('admin-panel/reports/pdf/', views.export_pdf, name='export_pdf'),
]
