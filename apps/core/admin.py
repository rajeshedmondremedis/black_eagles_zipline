from django.contrib import admin
from apps.core.models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'phone_number', 'email_address', 'updated_at')

    def has_add_permission(self, request):
        # Disallow creating multiple settings records
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

