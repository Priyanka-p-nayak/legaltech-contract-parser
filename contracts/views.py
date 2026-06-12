from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db import DatabaseError

from .models import Document, ExtractedClause, RiskFlag
from .serializers import (
    DocumentListSerializer,
    DocumentDetailSerializer,
    DocumentUploadSerializer,
    DocumentStatusUpdateSerializer,
    ExtractedClauseSerializer,
    RiskFlagSerializer,
)
from .validators import (
    validate_pdf_file,
    validate_document_status,
    validate_request_body,
)
from .exceptions import (
    DocumentNotFoundException,
    DatabaseOperationException,
)
from .pagination import StandardPagination, SmallPagination


# ============================================================
# HELPER: Standard API Response
# ============================================================

def api_response(
    success,
    message,
    data=None,
    status_code=status.HTTP_200_OK
):
    """
    Every API returns this same structure:
    {
        "success":     true/false,
        "message":     "description",
        "status_code": 200/201/400/404/500,
        "data":        { ... }
    }
    """
    body = {
        "success":     success,
        "message":     message,
        "status_code": status_code,
    }
    if data is not None:
        body["data"] = data
    return Response(body, status=status_code)


# ============================================================
# VIEW 1: HEALTH CHECK
# GET /api/v1/health/
# ============================================================

class HealthCheckView(APIView):
    """Health check — confirms API is running."""

    def get(self, request):
        return api_response(
            success=True,
            message="LegalTech API is running successfully.",
            data={
                "api_version":      "1.0.0",
                "status":           "healthy",
                "total_documents":  Document.objects.count(),
                "total_clauses":    ExtractedClause.objects.count(),
                "total_risk_flags": RiskFlag.objects.count(),
                "endpoints": {
                    "upload":         "POST  /api/v1/documents/upload/",
                    "list":           "GET   /api/v1/documents/",
                    "detail":         "GET   /api/v1/documents/{id}/",
                    "summary":        "GET   /api/v1/documents/{id}/summary/",
                    "update_status":  "PATCH /api/v1/documents/{id}/update-status/",
                    "clauses":        "POST/GET /api/v1/documents/{id}/clauses/",
                    "risks":          "POST/GET /api/v1/documents/{id}/risks/",
                    "nlp_pending":    "GET   /api/v1/nlp/documents/pending/",
                    "nlp_fetch":      "GET   /api/v1/nlp/documents/{id}/",
                    "nlp_process":    "POST  /api/v1/nlp/documents/{id}/process/",
                    "nlp_status":     "PATCH /api/v1/nlp/documents/{id}/status/",
                    "nlp_results":    "GET   /api/v1/nlp/documents/{id}/results/",
                    "stats":          "GET   /api/v1/stats/",
                }
            }
        )


# ============================================================
# VIEW 2: PDF UPLOAD
# POST /api/v1/documents/upload/
# ============================================================

class DocumentUploadView(APIView):
    """Upload a new PDF contract document."""

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):

        file = request.FILES.get('file', None)
        validate_pdf_file(file)

        serializer = DocumentUploadSerializer(data=request.data)

        if serializer.is_valid():
            try:
                document = serializer.save()
            except DatabaseError:
                raise DatabaseOperationException()

            return api_response(
                success=True,
                message=(
                    f"'{document.file_name}' uploaded successfully. "
                    f"Ready for NLP processing."
                ),
                data=DocumentDetailSerializer(document).data,
                status_code=status.HTTP_201_CREATED
            )

        return api_response(
            success=False,
            message="Upload failed. Please check errors below.",
            data={"errors": serializer.errors},
            status_code=status.HTTP_400_BAD_REQUEST
        )


# ============================================================
# VIEW 3: DOCUMENT LIST WITH PAGINATION
# GET /api/v1/documents/
# ============================================================

class DocumentListView(APIView):
    """List all documents with pagination and filtering."""

    parser_classes  = [JSONParser]

    def get(self, request):

        documents = Document.objects.all()

        # ── Filter: status ─────────────────────────────────
        status_filter = request.query_params.get('status', None)
        if status_filter:
            validate_document_status(status_filter)
            documents = documents.filter(status=status_filter)

        # ── Filter: contract_type ──────────────────────────
        contract_type = request.query_params.get('contract_type', None)
        if contract_type:
            documents = documents.filter(
                contract_type__icontains=contract_type
            )

        # ── Search ─────────────────────────────────────────
        search = request.query_params.get('search', None)
        if search:
            from django.db.models import Q
            documents = documents.filter(
                Q(file_name__icontains=search) |
                Q(counterparty_name__icontains=search)
            )

        # ── Ordering ───────────────────────────────────────
        allowed_orderings = [
            'uploaded_at',  '-uploaded_at',
            'risk_score',   '-risk_score',
        ]
        ordering = request.query_params.get('ordering', '-uploaded_at')
        if ordering in allowed_orderings:
            documents = documents.order_by(ordering)

        # ── Pagination ─────────────────────────────────────
        paginator   = StandardPagination()
        page        = paginator.paginate_queryset(documents, request)

        if page is not None:
            serializer = DocumentListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        # Fallback if pagination is disabled
        serializer = DocumentListSerializer(documents, many=True)
        return api_response(
            success=True,
            message=f"{documents.count()} document(s) found.",
            data={
                "count":     documents.count(),
                "documents": serializer.data,
            }
        )


# ============================================================
# VIEW 4: DOCUMENT DETAIL
# GET /api/v1/documents/{id}/
# ============================================================

class DocumentDetailView(APIView):
    """Full detail of one document including clauses and risks."""

    parser_classes = [JSONParser]

    def get(self, request, pk):

        document   = get_object_or_404(Document, pk=pk)
        serializer = DocumentDetailSerializer(document)

        return api_response(
            success=True,
            message=f"Document '{document.file_name}' retrieved successfully.",
            data=serializer.data
        )


# ============================================================
# VIEW 5: DOCUMENT STATUS UPDATE
# PATCH /api/v1/documents/{id}/update-status/
# ============================================================

class DocumentStatusUpdateView(APIView):
    """Update document status and metadata."""

    parser_classes = [JSONParser]

    def patch(self, request, pk):

        validate_request_body(request.data)
        document = get_object_or_404(Document, pk=pk)

        if 'status' in request.data:
            validate_document_status(request.data['status'])

        serializer = DocumentStatusUpdateSerializer(
            document,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            try:
                serializer.save()
            except DatabaseError:
                raise DatabaseOperationException()

            return api_response(
                success=True,
                message=(
                    f"Document '{document.file_name}' "
                    f"status updated successfully."
                ),
                data=serializer.data
            )

        return api_response(
            success=False,
            message="Status update failed. Please check errors below.",
            data={"errors": serializer.errors},
            status_code=status.HTTP_400_BAD_REQUEST
        )


# ============================================================
# VIEW 6: SAVE + GET EXTRACTED CLAUSES
# POST /api/v1/documents/{id}/clauses/
# GET  /api/v1/documents/{id}/clauses/
# ============================================================

class ExtractedClauseCreateView(APIView):
    """Save and retrieve extracted clauses for a document."""

    parser_classes = [JSONParser]

    def post(self, request, pk):

        validate_request_body(request.data)
        document = get_object_or_404(Document, pk=pk)

        # ── Bulk save ──────────────────────────────────────
        if isinstance(request.data, list):

            if len(request.data) == 0:
                return api_response(
                    success=False,
                    message="Empty list. Please send at least one clause.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            saved  = []
            errors = []

            for index, clause_data in enumerate(request.data):
                clause_data['document'] = document.id
                serializer = ExtractedClauseSerializer(data=clause_data)

                if serializer.is_valid():
                    try:
                        serializer.save()
                        saved.append(serializer.data)
                    except DatabaseError:
                        errors.append({
                            "index":  index,
                            "errors": "Database error saving clause."
                        })
                else:
                    errors.append({
                        "index":  index,
                        "errors": serializer.errors
                    })

            if errors:
                return api_response(
                    success=False,
                    message=(
                        f"{len(saved)} saved, "
                        f"{len(errors)} failed."
                    ),
                    data={"saved": saved, "errors": errors},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            return api_response(
                success=True,
                message=f"{len(saved)} clause(s) saved successfully.",
                data={"count": len(saved), "clauses": saved},
                status_code=status.HTTP_201_CREATED
            )

        # ── Single save ────────────────────────────────────
        data             = request.data.copy()
        data['document'] = document.id
        serializer       = ExtractedClauseSerializer(data=data)

        if serializer.is_valid():
            try:
                serializer.save()
            except DatabaseError:
                raise DatabaseOperationException()

            return api_response(
                success=True,
                message="Clause saved successfully.",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED
            )

        return api_response(
            success=False,
            message="Failed to save clause. Please check errors.",
            data={"errors": serializer.errors},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    def get(self, request, pk):

        document = get_object_or_404(Document, pk=pk)
        clauses  = ExtractedClause.objects.filter(document=document)

        # Optional filter
        clause_type = request.query_params.get('clause_type', None)
        if clause_type:
            clauses = clauses.filter(
                clause_type__icontains=clause_type
            )

        # Pagination
        paginator = SmallPagination()
        page      = paginator.paginate_queryset(clauses, request)

        if page is not None:
            serializer = ExtractedClauseSerializer(page, many=True)
            return Response({
                "success":     True,
                "message":     f"{clauses.count()} clause(s) found.",
                "status_code": 200,
                "data": {
                    "document_id": pk,
                    "total_count": clauses.count(),
                    "page_size":   paginator.get_page_size(request),
                    "next":        paginator.get_next_link(),
                    "previous":    paginator.get_previous_link(),
                    "clauses":     serializer.data,
                }
            })

        serializer = ExtractedClauseSerializer(clauses, many=True)
        return api_response(
            success=True,
            message=f"{clauses.count()} clause(s) found.",
            data={
                "document_id": pk,
                "count":       clauses.count(),
                "clauses":     serializer.data,
            }
        )


# ============================================================
# VIEW 7: SAVE + GET RISK FLAGS
# POST /api/v1/documents/{id}/risks/
# GET  /api/v1/documents/{id}/risks/
# ============================================================

class RiskFlagCreateView(APIView):
    """Save and retrieve risk flags for a document."""

    parser_classes = [JSONParser]

    def post(self, request, pk):

        validate_request_body(request.data)
        document = get_object_or_404(Document, pk=pk)

        # ── Bulk save ──────────────────────────────────────
        if isinstance(request.data, list):

            if len(request.data) == 0:
                return api_response(
                    success=False,
                    message="Empty list. Please send at least one risk flag.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            saved  = []
            errors = []

            for index, risk_data in enumerate(request.data):
                risk_data['document'] = document.id
                serializer = RiskFlagSerializer(data=risk_data)

                if serializer.is_valid():
                    try:
                        serializer.save()
                        saved.append(serializer.data)
                    except DatabaseError:
                        errors.append({
                            "index":  index,
                            "errors": "Database error saving risk flag."
                        })
                else:
                    errors.append({
                        "index":  index,
                        "errors": serializer.errors
                    })

            if errors:
                return api_response(
                    success=False,
                    message=(
                        f"{len(saved)} saved, "
                        f"{len(errors)} failed."
                    ),
                    data={"saved": saved, "errors": errors},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            return api_response(
                success=True,
                message=f"{len(saved)} risk flag(s) saved successfully.",
                data={"count": len(saved), "risk_flags": saved},
                status_code=status.HTTP_201_CREATED
            )

        # ── Single save ────────────────────────────────────
        data             = request.data.copy()
        data['document'] = document.id
        serializer       = RiskFlagSerializer(data=data)

        if serializer.is_valid():
            try:
                serializer.save()
            except DatabaseError:
                raise DatabaseOperationException()

            return api_response(
                success=True,
                message="Risk flag saved successfully.",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED
            )

        return api_response(
            success=False,
            message="Failed to save risk flag. Please check errors.",
            data={"errors": serializer.errors},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    def get(self, request, pk):

        document = get_object_or_404(Document, pk=pk)
        risks    = RiskFlag.objects.filter(document=document)

        # Optional filter
        severity = request.query_params.get('severity', None)
        if severity:
            risks = risks.filter(severity=severity)

        # Pagination
        paginator = SmallPagination()
        page      = paginator.paginate_queryset(risks, request)

        if page is not None:
            serializer = RiskFlagSerializer(page, many=True)
            return Response({
                "success":     True,
                "message":     f"{risks.count()} risk flag(s) found.",
                "status_code": 200,
                "data": {
                    "document_id": pk,
                    "total_count": risks.count(),
                    "page_size":   paginator.get_page_size(request),
                    "next":        paginator.get_next_link(),
                    "previous":    paginator.get_previous_link(),
                    "risk_flags":  serializer.data,
                }
            })

        serializer = RiskFlagSerializer(risks, many=True)
        return api_response(
            success=True,
            message=f"{risks.count()} risk flag(s) found.",
            data={
                "document_id": pk,
                "count":       risks.count(),
                "risk_flags":  serializer.data,
            }
        )


# ============================================================
# VIEW 8: DOCUMENT SUMMARY
# GET /api/v1/documents/{id}/summary/
# ============================================================

class DocumentSummaryView(APIView):
    """Quick summary for dashboard cards."""

    parser_classes = [JSONParser]

    def get(self, request, pk):

        document = get_object_or_404(Document, pk=pk)

        high   = document.risk_flags.filter(severity='high').count()
        medium = document.risk_flags.filter(severity='medium').count()
        low    = document.risk_flags.filter(severity='low').count()

        clause_breakdown = {}
        for clause in document.clauses.all():
            ct = clause.clause_type
            clause_breakdown[ct] = clause_breakdown.get(ct, 0) + 1

        return api_response(
            success=True,
            message="Document summary retrieved successfully.",
            data={
                "id":                document.id,
                "file_name":         document.file_name,
                "contract_type":     document.contract_type,
                "counterparty_name": document.counterparty_name,
                "governing_law":     document.governing_law,
                "status":            document.status,
                "uploaded_at":       document.uploaded_at,
                "risk_summary": {
                    "total":  document.risk_flags.count(),
                    "high":   high,
                    "medium": medium,
                    "low":    low,
                },
                "clause_summary": {
                    "total":     document.clauses.count(),
                    "breakdown": clause_breakdown,
                },
            }
        )


# ============================================================
# VIEW 9: OVERALL STATS
# GET /api/v1/stats/
# ============================================================

class StatsView(APIView):
    """Overall system statistics."""

    parser_classes = [JSONParser]

    def get(self, request):

        from django.db.models import Count

        status_breakdown = (
            Document.objects
            .values('status')
            .annotate(count=Count('id'))
        )

        severity_breakdown = (
            RiskFlag.objects
            .values('severity')
            .annotate(count=Count('id'))
        )

        type_breakdown = (
            Document.objects
            .exclude(contract_type__isnull=True)
            .values('contract_type')
            .annotate(count=Count('id'))
        )

        return api_response(
            success=True,
            message="Statistics retrieved successfully.",
            data={
                "total_documents":     Document.objects.count(),
                "total_clauses":       ExtractedClause.objects.count(),
                "total_risk_flags":    RiskFlag.objects.count(),
                "documents_by_status": list(status_breakdown),
                "risks_by_severity":   list(severity_breakdown),
                "documents_by_type":   list(type_breakdown),
            }
        )