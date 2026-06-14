from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# ============================================================
# MAIN PROJECT URL CONFIGURATION
#
# URL Structure:
#   /admin/          → Django Admin panel
#   /api/v1/         → All API endpoints (version 1)
# ============================================================

urlpatterns = [
    # Django Admin Panel
    path('admin/', admin.site.urls),

    # All API v1 endpoints
    path('api/v1/', include('contracts.urls', namespace='contracts')),
]

# Media Files (Development only)
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )