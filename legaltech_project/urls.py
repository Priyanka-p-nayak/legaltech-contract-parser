"""
urls.py
=======
Root URL configuration for the entire Django project.

Mounts:
  /admin/      → Django Admin panel
  /api/v1/     → All API endpoints (delegated to contracts/urls.py)
  /media/...   → Uploaded PDFs (development only, see DEBUG check)

Also registers custom 404/500 handlers from error_handlers.py
so even routing-level errors return our standard JSON shape
instead of Django's default HTML error pages.
"""


from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# ============================================================
# MAIN URL CONFIGURATION
# ============================================================

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        'api/v1/',
        include('contracts.urls', namespace='contracts')
    ),
]

# Serve uploaded files in development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

# ─ Custom Error Handlers ──────────────────────────────────
# These handle errors at Django level (not DRF level)
handler404 = 'legaltech_project.error_handlers.handler404'
handler500 = 'legaltech_project.error_handlers.handler500'