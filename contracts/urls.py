from django.urls import path
from . import views

app_name = 'contracts'

urlpatterns = [
    # Health & Stats
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
    path('stats/', views.StatsView.as_view(), name='stats'),

    # Document Endpoints
    path('documents/upload/', views.DocumentUploadView.as_view(), name='document-upload'),
    path('documents/', views.DocumentListView.as_view(), name='document-list'),
    path('documents/<int:pk>/', views.DocumentDetailView.as_view(), name='document-detail'),
    path('documents/<int:pk>/update-status/', views.DocumentStatusUpdateView.as_view(), name='document-update-status'),
    path('documents/<int:pk>/summary/', views.DocumentSummaryView.as_view(), name='document-summary'),

    # Clause & Risk Endpoints
    path('documents/<int:pk>/clauses/', views.ExtractedClauseCreateView.as_view(), name='document-clauses'),
    path('documents/<int:pk>/risks/', views.RiskFlagCreateView.as_view(), name='document-risks'),
]