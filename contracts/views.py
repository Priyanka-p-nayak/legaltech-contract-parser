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


# ============================================================
# HELPER FUNCTION
# Standard API response format for all endpoints
# ============================================================

def api_response(success, message, data=None, status_code=status.HTTP_200_OK):
    """
    Every API response follows this structure:
    {
        "success": true/false,
        "message": "description",
        "data": { ... }
    }
    """
    response_body = {
        "success":    success,
        "message":    message,
        "status_code": status_code,
    }
    if data is not None:
        response_body["data"] = data
    return Response(response_body, status=status_code)


# ============================================================
# VIEW 1: HEALTH CHECK
# GET /api/health/
# ============================================================

class HealthCheckView(APIView):
    """Health check endpoint."""

    def get(self, request):
        return api_response(
            success=True,
            message="LegalTech API is running successfully.",
            data={
                "api_version": "1.0.0",
                "status": "healthy",
                "total_documents":  Document.objects.count(),
                "total_clauses":    ExtractedClause.objects.count(),
                "total_risk_flags": RiskFlag.objects.count(),
                "endpoints": {
                    "upload_document":  "POST  /api/documents/upload/",
                    "list_documents":   "GET   /api/documents/",
                    "document_detail":  "GET   /api/documents/{id}/",
                    "update_status":    "PATCH /api/documents/{id}/update-status/",
                    "save_clauses":     "POST  /api/documents/{id}/clauses/",
                    "get_clauses":      "GET   /api/documents/{id}/clauses/",
                    "save_risks":       "POST  /api/documents/{id}/risks/",
                    "get_risks":        "GET   /api/documents/{id}/risks/",
                    "document_summary": "GET   /api/documents/{id}/summary/",
                    "stats":            "GET   /api/stats/",
                }
            }
        )


# ============================================================
# VIEW 2: PDF UPLOAD
# POST /api/documents/upload/
# ============================================================

class DocumentUploadView(APIView):
    """
    Upload a new PDF contract document.

    Method : POST
    URL    : /api/documents/upload/
    Body   : multipart/form-data
    Fields :
        file              (required) PDF file max 10MB
        contract_type     (optional) e.g. NDA, MSA
        counterparty_name (optional) e.g. Acme Corp
    """

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):

        # ── Validate file ──────────────────────────────────
        # validate_pdf_file raises exception automatically
        # if file is missing, not PDF, or too large
        file = request.FILES.get('file', None)
        validate_pdf_file(file)

        # ── Serialize and save ─────────────────────────────
        serializer = DocumentUploadSerializer(data=request.data)

        if serializer.is_valid():
            try:
                document = serializer.save()
            except DatabaseError:
                raise DatabaseOperationException()

            return api_response(
                success=True,
                message="PDF uploaded successfully. Ready for NLP processing.",
                data=DocumentDetailSerializer(document).data,
                status_code=status.HTTP_201_CREATED
            )

        # ── Serializer validation errors ───────────────────
        return api_response(
            success=False,
            message="Upload failed. Please check the errors below.",
            data={"errors": serializer.errors},
            status_code=status.HTTP_400_BAD_REQUEST
        )


# ============================================================
# VIEW 3: DOCUMENT LIST
# GET /api/documents/
# ============================================================

class DocumentListView(APIView):
    """
    List all uploaded documents with optional filtering.

    Query Parameters:
        status        uploaded | processing | completed | failed
        contract_type any string (case-insensitive)
        search        searches file_name and counterparty_name
        ordering      uploaded_at | -uploaded_at |
                      risk_score  | -risk_score
    """

    parser_classes = [JSONParser]

    def get(self, request):

        documents = Document.objects.all()

        # ── Filter: status ─────────────────────────────────
        status_filter = request.query_params.get('status', None)
        if status_filter:
            # This raises InvalidStatusException if invalid
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
            'uploaded_at', '-uploaded_at',
            'risk_score',  '-risk_score',
        ]
        ordering = request.query_params.get('ordering', '-uploaded_at')
        if ordering in allowed_orderings:
            documents = documents.order_by(ordering)

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
# GET /api/documents/{id}/
# ============================================================

class DocumentDetailView(APIView):
    """Full detail of one document including clauses and risks."""

    parser_classes = [JSONParser]

    def get(self, request, pk):

        document = get_object_or_404(Document, pk=pk)
        serializer = DocumentDetailSerializer(document)

        return api_response(
            success=True,
            message="Document retrieved successfully.",
            data=serializer.data
        )


# ============================================================
# VIEW 5: DOCUMENT STATUS UPDATE
# PATCH /api/documents/{id}/update-status/
# ============================================================

class DocumentStatusUpdateView(APIView):
    """
    Update document status and metadata after NLP processing.

    Method : PATCH
    URL    : /api/documents/{id}/update-status/
    """

    parser_classes = [JSONParser]

    def patch(self, request, pk):

        # Validate request body not empty
        validate_request_body(request.data)

        document = get_object_or_404(Document, pk=pk)

        # Validate status value if provided
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
                message="Document status updated successfully.",
                data=serializer.data
            )

        return api_response(
            success=False,
            message="Status update failed. Please check the errors below.",
            data={"errors": serializer.errors},
            status_code=status.HTTP_400_BAD_REQUEST
        )


# ============================================================
# VIEW 6: SAVE + GET EXTRACTED CLAUSES
# POST /api/documents/{id}/clauses/
# GET  /api/documents/{id}/clauses/
# ============================================================

class ExtractedClauseCreateView(APIView):
    """
    Save and retrieve extracted clauses.

    POST: Save one clause OR list of clauses
    GET : Get all clauses (optional ?clause_type= filter)
    """

    parser_classes = [JSONParser]

    def post(self, request, pk):

        # Validate request body
        validate_request_body(request.data)

        document = get_object_or_404(Document, pk=pk)

        # ── Bulk save ──────────────────────────────────────
        if isinstance(request.data, list):

            if len(request.data) == 0:
                return api_response(
                    success=False,
                    message="Empty list provided. Please send at least one clause.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            saved_clauses = []
            errors        = []

            for index, clause_data in enumerate(request.data):
                clause_data['document'] = document.id
                serializer = ExtractedClauseSerializer(data=clause_data)

                if serializer.is_valid():
                    try:
                        serializer.save()
                        saved_clauses.append(serializer.data)
                    except DatabaseError:
                        errors.append({
                            "index":  index,
                            "errors": "Database error while saving clause."
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
                        f"{len(saved_clauses)} clause(s) saved, "
                        f"{len(errors)} failed."
                    ),
                    data={"saved": saved_clauses, "errors": errors},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            return api_response(
                success=True,
                message=f"{len(saved_clauses)} clause(s) saved successfully.",
                data=saved_clauses,
                status_code=status.HTTP_201_CREATED
            )

        # ── Single save ────────────────────────────────────
        data = request.data.copy()
        data['document'] = document.id
        serializer = ExtractedClauseSerializer(data=data)

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
            message="Failed to save clause. Please check the errors.",
            data={"errors": serializer.errors},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    def get(self, request, pk):

        document = get_object_or_404(Document, pk=pk)

        clauses = ExtractedClause.objects.filter(document=document)

        # Optional filter by clause_type
        clause_type = request.query_params.get('clause_type', None)
        if clause_type:
            clauses = clauses.filter(clause_type__icontains=clause_type)

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
# POST /api/documents/{id}/risks/
# GET  /api/documents/{id}/risks/
# ============================================================

class RiskFlagCreateView(APIView):
    """
    Save and retrieve risk flags.

    POST: Save one risk flag OR list of risk flags
    GET : Get all risk flags (optional ?severity= filter)
    """

    parser_classes = [JSONParser]

    def post(self, request, pk):

        validate_request_body(request.data)

        document = get_object_or_404(Document, pk=pk)

        # ── Bulk save ──────────────────────────────────────
        if isinstance(request.data, list):

            if len(request.data) == 0:
                return api_response(
                    success=False,
                    message="Empty list provided. Please send at least one risk flag.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            saved_risks = []
            errors      = []

            for index, risk_data in enumerate(request.data):
                risk_data['document'] = document.id
                serializer = RiskFlagSerializer(data=risk_data)

                if serializer.is_valid():
                    try:
                        serializer.save()
                        saved_risks.append(serializer.data)
                    except DatabaseError:
                        errors.append({
                            "index":  index,
                            "errors": "Database error while saving risk flag."
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
                        f"{len(saved_risks)} risk(s) saved, "
                        f"{len(errors)} failed."
                    ),
                    data={"saved": saved_risks, "errors": errors},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            return api_response(
                success=True,
                message=f"{len(saved_risks)} risk flag(s) saved successfully.",
                data=saved_risks,
                status_code=status.HTTP_201_CREATED
            )

        # ── Single save ────────────────────────────────────
        data = request.data.copy()
        data['document'] = document.id
        serializer = RiskFlagSerializer(data=data)

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
            message="Failed to save risk flag. Please check the errors.",
            data={"errors": serializer.errors},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    def get(self, request, pk):

        document = get_object_or_404(Document, pk=pk)

        risks = RiskFlag.objects.filter(document=document)

        # Optional filter by severity
        severity = request.query_params.get('severity', None)
        if severity:
            risks = risks.filter(severity=severity)

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
# GET /api/documents/{id}/summary/
# ============================================================

class DocumentSummaryView(APIView):
    """Quick summary for dashboard display."""

    parser_classes = [JSONParser]

    def get(self, request, pk):

        document = get_object_or_404(Document, pk=pk)

        high_risks   = document.risk_flags.filter(severity='high').count()
        medium_risks = document.risk_flags.filter(severity='medium').count()
        low_risks    = document.risk_flags.filter(severity='low').count()

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
                    "high":   high_risks,
                    "medium": medium_risks,
                    "low":    low_risks,
                },
                "clause_summary": {
                    "total":     document.clauses.count(),
                    "breakdown": clause_breakdown,
                },
            }
        )


# ============================================================
# VIEW 9: OVERALL STATS
# GET /api/stats/
# ============================================================

class StatsView(APIView):
    """Overall system statistics for the dashboard."""

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