from django.urls import path
from . import views
from . import nlp_views

# ============================================================
# CONTRACTS APP — COMPLETE URL PATTERNS
# ============================================================

app_name = 'contracts'

urlpatterns = [

    # ══════════════════════════════════════════════════════
    # GENERAL ENDPOINTS
    # ══════════════════════════════════════════════════════

    # GET /api/health/
    path('health/', views.HealthCheckView.as_view(), name='health-check'),

    # GET /api/stats/
    path('stats/', views.StatsView.as_view(), name='stats'),

    # ══════════════════════════════════════════════════════
    # DOCUMENT ENDPOINTS (for Frontend / Member 3)
    # ══════════════════════════════════════════════════════

    # POST /api/documents/upload/
    path('documents/upload/', views.DocumentUploadView.as_view(), name='document-upload'),

    # GET /api/documents/
    path('documents/', views.DocumentListView.as_view(), name='document-list'),

    # GET /api/documents/{id}/
    path('documents/<int:pk>/', views.DocumentDetailView.as_view(), name='document-detail'),

    # GET /api/documents/{id}/summary/
    path('documents/<int:pk>/summary/', views.DocumentSummaryView.as_view(), name='document-summary'),

    # PATCH /api/documents/{id}/update-status/
    path('documents/<int:pk>/update-status/', views.DocumentStatusUpdateView.as_view(), name='document-update-status'),

    # POST/GET /api/documents/{id}/clauses/
    path('documents/<int:pk>/clauses/', views.ExtractedClauseCreateView.as_view(), name='document-clauses'),

    # POST/GET /api/documents/{id}/risks/
    path('documents/<int:pk>/risks/', views.RiskFlagCreateView.as_view(), name='document-risks'),

    # ══════════════════════════════════════════════════════
    # NLP INTEGRATION ENDPOINTS (for Member 2)
    # ══════════════════════════════════════════════════════

    # GET /api/nlp/documents/pending/
    path('nlp/documents/pending/', nlp_views.NLPPendingDocumentsView.as_view(), name='nlp-pending-documents'),

    # GET /api/nlp/documents/{id}/
    path('nlp/documents/<int:pk>/', nlp_views.NLPDocumentFetchView.as_view(), name='nlp-document-fetch'),

    # POST /api/nlp/documents/{id}/process/
    path('nlp/documents/<int:pk>/process/', nlp_views.NLPProcessResultView.as_view(), name='nlp-process-result'),

    # PATCH /api/nlp/documents/{id}/status/
    path('nlp/documents/<int:pk>/status/', nlp_views.NLPStatusUpdateView.as_view(), name='nlp-status-update'),

    # GET /api/nlp/documents/{id}/results/
    path('nlp/documents/<int:pk>/results/', nlp_views.NLPResultsView.as_view(), name='nlp-results'),
]