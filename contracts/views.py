"""
views.py
========
Dashboard-and-frontend-facing API views: document upload,
listing, detail, summary, status updates, and clause/risk
CRUD endpoints.

NLP-specific views (used by Member 2's module) live in the
separate nlp_views.py file — kept apart so each teammate's
integration surface is easy to find.

See docs/API_DOCUMENTATION.md for full endpoint reference
and docs/BUG_FIXES_DAY24.md for cross-module consistency
fixes applied to several views below.
"""

from django.db import DatabaseError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import DatabaseOperationException
from .models import Document, ExtractedClause, RiskFlag
from .pagination import SmallPagination, StandardPagination
from .serializers import (
    DocumentDetailSerializer,
    DocumentListSerializer,
    DocumentStatusUpdateSerializer,
    DocumentUploadSerializer,
    ExtractedClauseSerializer,
    RiskFlagSerializer,
)
from .validators import (
    sanitize_search_query,
    validate_document_status,
    validate_ordering,
    validate_pdf_file,
    validate_request_body,
)


# ============================================================
# HELPER: Standard API Response
# ============================================================

def api_response(
    success,
    message,
    data=None,
    status_code=status.HTTP_200_OK
):
    """Standard JSON response for all endpoints."""
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
                    "upload":        "POST  /api/v1/documents/upload/",
                    "list":          "GET   /api/v1/documents/",
                    "detail":        "GET   /api/v1/documents/{id}/",
                    "summary":       "GET   /api/v1/documents/{id}/summary/",
                    "update_status": "PATCH /api/v1/documents/{id}/update-status/",
                    "clauses":       "POST/GET /api/v1/documents/{id}/clauses/",
                    "risks":         "POST/GET /api/v1/documents/{id}/risks/",
                    "nlp_pending":   "GET   /api/v1/nlp/documents/pending/",
                    "nlp_fetch":     "GET   /api/v1/nlp/documents/{id}/",
                    "nlp_process":   "POST  /api/v1/nlp/documents/{id}/process/",
                    "nlp_status":    "PATCH /api/v1/nlp/documents/{id}/status/",
                    "nlp_results":   "GET   /api/v1/nlp/documents/{id}/results/",
                    "stats":         "GET   /api/v1/stats/",
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
# VIEW 3: DOCUMENT LIST
# GET /api/v1/documents/
# ============================================================

class DocumentListView(APIView):
    """List all documents with pagination."""

    parser_classes = [JSONParser]

    def get(self, request):
        # WHY prefetch_related here: DocumentListSerializer's
        # get_total_clauses/get_total_risks methods call
        # obj.total_clauses_count and obj.total_risks_count for
        # EVERY document in the page. Without prefetching, a page
        # of 10 documents triggers 20 extra queries (2 per doc).
        # With prefetch_related, it's just 2 extra queries TOTAL
        # for the whole page, regardless of page size.
        documents = Document.objects.all().prefetch_related(
            'clauses', 'risk_flags'
        )

        # ── Filter: status ─────────────────────────────────
        status_filter = request.query_params.get('status', None)
        if status_filter:
            validate_document_status(status_filter)
            documents = documents.filter(status=status_filter)

        # ── Filter: contract_type ──────────────────────────
        contract_type = request.query_params.get(
            'contract_type', None
        )
        if contract_type:
            contract_type = contract_type.strip()[:100]
            documents = documents.filter(
                contract_type__icontains=contract_type
            )

        # ── Search ─────────────────────────────────────────
        search = request.query_params.get('search', None)
        if search:
            search = sanitize_search_query(search)
            if search:
                documents = documents.filter(
                    Q(file_name__icontains=search) |
                    Q(counterparty_name__icontains=search)
                )

        # ── Ordering ───────────────────────────────────────
        # WHY this doesn't raise a 400 like the status filter does:
        # an invalid ordering value is a much lower-stakes mistake
        # than an invalid status filter — the user still gets
        # correct (just not custom-sorted) results. We surface a
        # "warning" field instead of failing the whole request.
        # See docs/BUG_FIXES_DAY24.md, Bug 6.
        ordering_param = request.query_params.get(
            'ordering', '-uploaded_at'
        )
        ordering         = validate_ordering(ordering_param)
        ordering_ignored = (
            ordering_param != ordering
            and ordering_param != '-uploaded_at'
        )
        documents = documents.order_by(ordering)

        # ── Pagination ─────────────────────────────────────
        paginator = StandardPagination()
        page      = paginator.paginate_queryset(documents, request)

        # Build a helpful warning if the ordering param was invalid
        warning = None
        if ordering_ignored:
            warning = (
                f"'{ordering_param}' is not a valid ordering value. "
                f"Falling back to default ordering (-uploaded_at). "
                f"Allowed values: uploaded_at, -uploaded_at, "
                f"risk_score, -risk_score."
            )

        if page is not None:
            serializer = DocumentListSerializer(page, many=True)
            response   = paginator.get_paginated_response(serializer.data)
            if warning:
                if 'data' in response.data:
                    response.data['data']['warning'] = warning
                else:
                    response.data['warning'] = warning
            return response

        serializer = DocumentListSerializer(documents, many=True)
        data = {
            "count":     documents.count(),
            "documents": serializer.data,
        }
        if warning:
            data["warning"] = warning

        return api_response(
            success=True,
            message=f"{documents.count()} document(s) found.",
            data=data
        )


# ============================================================
# VIEW 4: DOCUMENT DETAIL
# GET /api/v1/documents/{id}/
# ============================================================

class DocumentDetailView(APIView):
    """Full detail of one document."""

    parser_classes = [JSONParser]

    def get(self, request, pk):
        # WHY prefetch_related here: DocumentDetailSerializer
        # nests the FULL list of clauses and risk_flags (not just
        # counts) via ExtractedClauseSerializer/RiskFlagSerializer
        # many=True. Without prefetching, accessing
        # document.clauses.all() and document.risk_flags.all()
        # inside the serializer triggers 2 separate queries anyway
        # — but combined with total_clauses_count/total_risks_count
        # ALSO being called, that becomes 4 queries instead of 2.
        # prefetch_related ensures all 4 of those property/field
        # accesses share just 2 actual database queries.
        document = get_object_or_404(
            Document.objects.prefetch_related('clauses', 'risk_flags'),
            pk=pk
        )
        serializer = DocumentDetailSerializer(document)

        return api_response(
            success=True,
            message=(
                f"Document '{document.file_name}' "
                f"retrieved successfully."
            ),
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

        for date_field in [
            'contract_start_date',
            'contract_end_date'
        ]:
            if date_field in request.data:
                from .validators import validate_date_format
                try:
                    validate_date_format(
                        request.data[date_field]
                    )
                except ValueError as e:
                    return api_response(
                        success=False,
                        message=str(e),
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

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
            message="Update failed. Please check errors below.",
            data={"errors": serializer.errors},
            status_code=status.HTTP_400_BAD_REQUEST
        )


# ============================================================
# VIEW 6: SAVE + GET EXTRACTED CLAUSES
# POST /api/v1/documents/{id}/clauses/
# GET  /api/v1/documents/{id}/clauses/
# ============================================================

class ExtractedClauseCreateView(APIView):
    """Save and retrieve extracted clauses."""

    parser_classes = [JSONParser]

    def post(self, request, pk):

        validate_request_body(request.data)
        document = get_object_or_404(Document, pk=pk)

        # ── Bulk save ──────────────────────────────────────
        if isinstance(request.data, list):

            if len(request.data) == 0:
                return api_response(
                    success=False,
                    message=(
                        "Empty list provided. "
                        "Please send at least one clause."
                    ),
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Limit bulk size to 100 at once.
            # WHY 100: keeps a single request's database writes
            # fast and bounded. This SAME limit is enforced in
            # RiskFlagCreateView below and in nlp_views.py's
            # NLPProcessResultView (see docs/BUG_FIXES_DAY24.md,
            # Bug 5) — if you change this number, change it in
            # all three places.
            if len(request.data) > 100:
                return api_response(
                    success=False,
                    message=(
                        f"Too many clauses ({len(request.data)}). "
                        f"Maximum 100 per request."
                    ),
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            saved  = []
            errors = []

            for index, clause_data in enumerate(request.data):
                clause_data['document'] = document.id
                serializer = ExtractedClauseSerializer(
                    data=clause_data
                )
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
                message=(
                    f"{len(saved)} clause(s) saved successfully."
                ),
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

        document    = get_object_or_404(Document, pk=pk)
        clauses     = ExtractedClause.objects.filter(
            document=document
        )

        clause_type = request.query_params.get('clause_type', None)
        if clause_type:
            clause_type = clause_type.strip()[:50]
            clauses     = clauses.filter(
                clause_type__icontains=clause_type
            )

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
    """Save and retrieve risk flags."""

    parser_classes = [JSONParser]

    def post(self, request, pk):
        """POST /api/v1/documents/{id}/risks/ - Create risk flags."""

        validate_request_body(request.data)
        document = get_object_or_404(Document, pk=pk)

        # ── Bulk save ──────────────────────────────────────
        if isinstance(request.data, list):

            if len(request.data) == 0:
                return api_response(
                    success=False,
                    message=(
                        "Empty list provided. "
                        "Please send at least one risk flag."
                    ),
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if len(request.data) > 100:
                return api_response(
                    success=False,
                    message=(
                        f"Too many risk flags ({len(request.data)}). "
                        f"Maximum 100 per request."
                    ),
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
                            "errors": "Database error saving risk."
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
                message=(
                    f"{len(saved)} risk flag(s) saved successfully."
                ),
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
            message="Failed to save risk flag.",
            data={"errors": serializer.errors},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    def get(self, request, pk):
        """GET /api/v1/documents/{id}/risks/ - List all risk flags."""
        
        document = get_object_or_404(Document, pk=pk)
        risks = RiskFlag.objects.filter(document=document)

        # ── Severity Filter with Validation ─────────────────
        severity_param = request.query_params.get('severity', None)
        severity_warning = None

        if severity_param:
            severity_cleaned = severity_param.strip().lower()[:20]
            allowed_severities = ['low', 'medium', 'high']

            if severity_cleaned not in allowed_severities:
                # INVALID severity - set warning, DO NOT filter
                severity_warning = (
                    f"'{severity_param}' is not a valid severity. "
                    f"Allowed values: {', '.join(allowed_severities)}. "
                    f"No filter was applied."
                )
                # CRITICAL: Do NOT apply any filter here!
            else:
                # VALID severity - apply filter
                risks = risks.filter(severity=severity_cleaned)

        # ── Pagination ──────────────────────────────────────
        paginator = SmallPagination()
        page = paginator.paginate_queryset(risks, request)

        if page is not None:
            serializer = RiskFlagSerializer(page, many=True)
            
            # Build paginated response data
            paginated_data = {
                "document_id": pk,
                "total_count": paginator.page.paginator.count,
                "page_size": paginator.get_page_size(request),
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "risk_flags": serializer.data,
            }
            
            # Add warning if needed
            if severity_warning:
                paginated_data["warning"] = severity_warning
            
            return api_response(
                success=True,
                message=f"{risks.count()} risk flag(s) found.",
                data=paginated_data
            )

        # ── Non-paginated response (fallback) ───────────────
        serializer = RiskFlagSerializer(risks, many=True)
        data = {
            "document_id": pk,
            "count": risks.count(),
            "risk_flags": serializer.data,
        }
        if severity_warning:
            data["warning"] = severity_warning

        return api_response(
            success=True,
            message=f"{risks.count()} risk flag(s) found.",
            data=data
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

        # ── Status Breakdown ───────────────────────────────
        # Always include all 4 statuses even when count is 0
        status_counts_raw = {
            row['status']: row['count']
            for row in Document.objects.values('status')
                                        .annotate(count=Count('id'))
        }
        status_breakdown = [
            {"status": "uploaded",   "count": status_counts_raw.get('uploaded', 0)},
            {"status": "processing", "count": status_counts_raw.get('processing', 0)},
            {"status": "completed",  "count": status_counts_raw.get('completed', 0)},
            {"status": "failed",     "count": status_counts_raw.get('failed', 0)},
        ]

        # ── Risk Severity Breakdown ────────────────────────
        # Always include all 3 severities even when count is 0
        severity_counts_raw = {
            row['severity']: row['count']
            for row in RiskFlag.objects.values('severity')
                                        .annotate(count=Count('id'))
        }
        severity_breakdown = [
            {"severity": "high",   "count": severity_counts_raw.get('high', 0)},
            {"severity": "medium", "count": severity_counts_raw.get('medium', 0)},
            {"severity": "low",    "count": severity_counts_raw.get('low', 0)},
        ]

        # ── Contract Type Breakdown ────────────────────────
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
                "documents_by_status": status_breakdown,
                "risks_by_severity":   severity_breakdown,
                "documents_by_type":   list(type_breakdown),
            }
        )


# ============================================================
# VIEW 10: DASHBOARD OVERVIEW
# GET /api/v1/dashboard/
# ============================================================

class DashboardOverviewView(APIView):
    """Single endpoint for dashboard overview page."""

    parser_classes = [JSONParser]

    def get(self, request):

        # ── Total Counts ───────────────────────────────────
        total_documents  = Document.objects.count()
        total_clauses    = ExtractedClause.objects.count()
        total_risks      = RiskFlag.objects.count()
        total_resolved   = RiskFlag.objects.filter(
            is_resolved=True
        ).count()
        total_unresolved = RiskFlag.objects.filter(
            is_resolved=False
        ).count()

        # ── Status Breakdown ───────────────────────────────
        status_counts = {
            'uploaded':   Document.objects.filter(
                status='uploaded'
            ).count(),
            'processing': Document.objects.filter(
                status='processing'
            ).count(),
            'completed':  Document.objects.filter(
                status='completed'
            ).count(),
            'failed':     Document.objects.filter(
                status='failed'
            ).count(),
        }

        # ── Risk Severity Breakdown ────────────────────────
        risk_counts = {
            'high':   RiskFlag.objects.filter(
                severity='high'
            ).count(),
            'medium': RiskFlag.objects.filter(
                severity='medium'
            ).count(),
            'low':    RiskFlag.objects.filter(
                severity='low'
            ).count(),
        }

        # ── Recent Documents (last 5) ──────────────────────
        # WHY prefetch_related here: total_clauses_count and
        # total_risks_count each trigger a separate .count()
        # query per document (N+1 problem). prefetch_related
        # loads ALL clauses and risk_flags for these 5 documents
        # in just 2 extra queries total, then total_clauses_count
        # /total_risks_count use the already-loaded data instead
        # of hitting the database again. See Day 29 optimization.
        recent_docs = Document.objects.all().prefetch_related(
            'clauses', 'risk_flags'
        )[:5]
        recent_documents_data = []

        for doc in recent_docs:
            recent_documents_data.append({
                "id":                doc.id,
                "file_name":         doc.file_name,
                "contract_type":     doc.contract_type,
                "counterparty_name": doc.counterparty_name,
                "status":            doc.status,
                "risk_score":        doc.risk_score,
                "uploaded_at":       doc.uploaded_at,
                # .count() on a prefetched manager uses Python's
                # len() on the cached queryset instead of issuing
                # a new SQL query — that's the whole optimization.
                "total_clauses":     doc.clauses.count(),
                "total_risks":       doc.risk_flags.count(),
            })

        # ── Recent High Risk Flags (last 5) ───────────────
        # select_related('document') was already correct here
        # (added Day 22) — each risk needs risk.document.file_name,
        # and select_related joins that in the SAME query instead
        # of a separate query per risk. Verified during Day 29
        # optimization pass — no change needed.
        recent_high_risks = RiskFlag.objects.filter(
            severity='high',
            is_resolved=False
        ).select_related('document')[:5]

        recent_risks_data = []
        for risk in recent_high_risks:
            recent_risks_data.append({
                "id":            risk.id,
                "risk_title":    risk.risk_title,
                "severity":      risk.severity,
                "document_id":   risk.document.id,
                "document_name": risk.document.file_name,
                "page_number":   risk.page_number,
                "is_resolved":   risk.is_resolved,
                "flagged_at":    risk.flagged_at,
            })

        # ── Contract Type Breakdown ────────────────────────
        contract_types = (
            Document.objects
            .exclude(contract_type__isnull=True)
            .exclude(contract_type='')
            .values('contract_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        return api_response(
            success=True,
            message="Dashboard data retrieved successfully.",
            data={
                "summary": {
                    "total_documents":   total_documents,
                    "total_clauses":     total_clauses,
                    "total_risks":       total_risks,
                    "total_resolved":    total_resolved,
                    "total_unresolved":  total_unresolved,
                },
                "status_breakdown":        status_counts,
                "risk_breakdown":          risk_counts,
                "contract_type_breakdown": list(contract_types),
                "recent_documents":        recent_documents_data,
                "recent_high_risks":       recent_risks_data,
            }
        )