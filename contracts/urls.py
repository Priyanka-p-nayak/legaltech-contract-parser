"""
urls.py
=======
URL routing for the contracts app.
All URLs here are mounted under /api/v1/ by the main project's urls.py.
"""

from django.urls import path
from . import views
from . import nlp_views

# ============================================================
# CONTRACTS APP — URL PATTERNS
# ============================================================
app_name = 'contracts'

urlpatterns = [
    # ── Utility Endpoints ──────────────────────────────────
    path('health/',
         views.HealthCheckView.as_view(),
         name='health-check'),
    path('stats/',
         views.StatsView.as_view(),
         name='stats'),

    # ── Document Endpoints ─────────────────────────────────
    path('documents/upload/',
         views.DocumentUploadView.as_view(),
         name='document-upload'),
    path('documents/',
         views.DocumentListView.as_view(),
         name='document-list'),
    path('documents/<int:pk>/',
         views.DocumentDetailView.as_view(),
         name='document-detail'),
    path('documents/<int:pk>/summary/',
         views.DocumentSummaryView.as_view(),
         name='document-summary'),
    path('documents/<int:pk>/update-status/',
         views.DocumentStatusUpdateView.as_view(),
         name='document-update-status'),
    path('documents/<int:pk>/clauses/',
         views.ExtractedClauseCreateView.as_view(),
         name='document-clauses'),
    path('documents/<int:pk>/risks/',
         views.RiskFlagCreateView.as_view(),
         name='document-risks'),

    # ── Dashboard Endpoint ─────────────────────────────────
    path('dashboard/',
         views.DashboardOverviewView.as_view(),
         name='dashboard-overview'),

    # ── NLP Integration Endpoints ──────────────────────────
    path('nlp/documents/pending/',
         nlp_views.NLPPendingDocumentsView.as_view(),
         name='nlp-pending-documents'),
    path('nlp/documents/<int:pk>/',
         nlp_views.NLPDocumentFetchView.as_view(),
         name='nlp-document-fetch'),
    path('nlp/documents/<int:pk>/process/',
         nlp_views.NLPProcessResultView.as_view(),
         name='nlp-process-result'),
    path('nlp/documents/<int:pk>/status/',
         nlp_views.NLPStatusUpdateView.as_view(),
         name='nlp-status-update'),
    path('nlp/documents/<int:pk>/results/',
         nlp_views.NLPResultsView.as_view(),
         name='nlp-results'),
]