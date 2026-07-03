"""
urls.py
=======
Root URL configuration for the LegalTech project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from importlib import import_module

try:
    admin_dashboard_stats = import_module('contracts.views_admin').admin_dashboard_stats
except Exception:
    # Fallback stub view if the real admin dashboard view cannot be imported.
    from django.http import HttpResponseNotFound

    def admin_dashboard_stats(request, *args, **kwargs):
        return HttpResponseNotFound('Admin stats view not available')

urlpatterns = [

    # Django Admin panel
    path('admin/', admin.site.urls),

    # Custom admin statistics dashboard
    path(
        'admin/stats/',
        admin_dashboard_stats,
        name='admin-stats-dashboard'
    ),

    # All REST API endpoints
    path(
        'api/v1/',
        include('contracts.urls', namespace='contracts')
    ),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

handler404 = 'legaltech_project.error_handlers.handler404'
handler500 = 'legaltech_project.error_handlers.handler500'