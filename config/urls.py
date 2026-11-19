from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

def sw_view(request):
    """
    Handles browser queries for /sw.js (e.g. from previous localhost PWA/service-worker registrations).
    Instructs the browser to cleanly unregister any stale service worker from other localhost projects.
    """
    content = (
        "self.addEventListener('install', () => self.skipWaiting());\n"
        "self.addEventListener('activate', () => self.registration.unregister());\n"
    )
    return HttpResponse(content, content_type='application/javascript')

def favicon_view(request):
    """
    Silently handles /favicon.ico queries with 204 No Content if not provided by static files.
    """
    return HttpResponse(status=204)

urlpatterns = [
    path('sw.js', sw_view, name='service_worker'),
    path('favicon.ico', favicon_view, name='favicon'),
    path('django-admin/', admin.site.urls),
    path('', include('apps.website.urls')),
    path('', include('apps.bookings.urls')),
    path('', include('apps.dashboard.urls')),
    path('', include('apps.reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
