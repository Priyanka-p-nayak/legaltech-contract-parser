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