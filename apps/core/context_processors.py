from apps.core.models import SiteSettings


def site_settings(request):
    try:
        return {'site_settings': SiteSettings.get_settings()}
    except Exception:
        return {'site_settings': None}

