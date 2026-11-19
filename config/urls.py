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

def robots_txt_view(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin-panel/",
        "Disallow: /django-admin/",
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

def sitemap_xml_view(request):
    host = f"{request.scheme}://{request.get_host()}"
    routes = [
        '',
        '/about/',
        '/gallery/',
        '/pricing/',
        '/safety/',
        '/contact/',
        '/book/',
        '/booking/lookup/',
    ]
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for r in routes:
        xml_lines.append(f'  <url><loc>{host}{r}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>')
    xml_lines.append('</urlset>')
    return HttpResponse("\n".join(xml_lines), content_type="application/xml")

urlpatterns = [
    path('sw.js', sw_view, name='service_worker'),
    path('favicon.ico', favicon_view, name='favicon'),
    path('robots.txt', robots_txt_view, name='robots_txt'),
    path('sitemap.xml', sitemap_xml_view, name='sitemap_xml'),
    path('django-admin/', admin.site.urls),
    path('', include('apps.website.urls')),
    path('', include('apps.bookings.urls')),
    path('', include('apps.dashboard.urls')),
    path('', include('apps.reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
