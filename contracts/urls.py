from django.urls import path
from . import views
from . import nlp_views

# ============================================================
# CONTRACTS APP — FINAL URL PATTERNS
# Base prefix: /api/v1/ (set in main urls.py)
#
# NAMING CONVENTION:
# - List endpoints   : resource-list
# - Detail endpoints : resource-detail
# - Action endpoints : resource-action-name
# ============================================================

app_name = 'contracts'

urlpatterns = [

    # ══════════════════════════════════════════════════════
    # UTILITY ENDPOINTS
    # ══════════════════════════════════════════════════════

    # GET /api/v1/health/
    path('health/', views.HealthCheckView.as_view(), name='health-check'),

    # GET /api/v1/stats/
    path('stats/', views.StatsView.as_view(), name='stats'),

    # ══════════════════════════════════════════════════════
    # DOCUMENT ENDPOINTS
    # Used by: Member 3 Dashboard + Paralegal users
    # ══════════════════════════════════════════════════════

    # POST /api/v1/documents/upload/
    path('documents/upload/', views.DocumentUploadView.as_view(), name='document-upload'),

    # GET /api/v1/documents/
    path('documents/', views.DocumentListView.as_view(), name='document-list'),

    # GET /api/v1/documents/{id}/
    path('documents/<int:pk>/', views.DocumentDetailView.as_view(), name='document-detail'),

    # GET /api/v1/documents/{id}/summary/
    path('documents/<int:pk>/summary/', views.DocumentSummaryView.as_view(), name='document-summary'),

    # PATCH /api/v1/documents/{id}/update-status/
    path('documents/<int:pk>/update-status/', views.DocumentStatusUpdateView.as_view(), name='document-update-status'),

    # POST/GET /api/v1/documents/{id}/clauses/
    path('documents/<int:pk>/clauses/', views.ExtractedClauseCreateView.as_view(), name='document-clauses'),

    # POST/GET /api/v1/documents/{id}/risks/
    path('documents/<int:pk>/risks/', views.RiskFlagCreateView.as_view(), name='document-risks'),

    # ══════════════════════════════════════════════════════
    # NLP INTEGRATION ENDPOINTS
    # Used by: Member 2 (NLP/spaCy module)
    # ══════════════════════════════════════════════════════

    # GET /api/v1/nlp/documents/pending/
    path('nlp/documents/pending/', nlp_views.NLPPendingDocumentsView.as_view(), name='nlp-pending-documents'),

    # GET /api/v1/nlp/documents/{id}/
    path('nlp/documents/<int:pk>/', nlp_views.NLPDocumentFetchView.as_view(), name='nlp-document-fetch'),

    # POST /api/v1/nlp/documents/{id}/process/
    path('nlp/documents/<int:pk>/process/', nlp_views.NLPProcessResultView.as_view(), name='nlp-process-result'),

    # PATCH /api/v1/nlp/documents/{id}/status/
    path('nlp/documents/<int:pk>/status/', nlp_views.NLPStatusUpdateView.as_view(), name='nlp-status-update'),

    # GET /api/v1/nlp/documents/{id}/results/
    path('nlp/documents/<int:pk>/results/', nlp_views.NLPResultsView.as_view(), name='nlp-results'),
]