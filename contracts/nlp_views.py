"""
nlp_views.py
============
NLP integration API views — the entire surface area Member 2's
NLP module (PyMuPDF + spaCy) talks to.

Kept in a separate file from views.py intentionally, so Member 2
only ever needs to look at ONE file to understand every endpoint
they can call. See docs/MEMBER3_GUIDE.md's counterpart for
Member 3 (that guide points mainly at views.py's endpoints
instead).

Five views:
  1. NLPPendingDocumentsView — "what work is left?"
  2. NLPDocumentFetchView    — "give me this doc's file path"
  3. NLPProcessResultView    — "here are my results" (main call)
  4. NLPStatusUpdateView     — "mark this as processing"
  5. NLPResultsView          — "let me verify what was saved"
"""

from django.db import DatabaseError, transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import DatabaseOperationException, DocumentAlreadyProcessedException
from .models import Document, ExtractedClause, RiskFlag
from .serializers import ExtractedClauseSerializer, RiskFlagSerializer
from .validators import validate_document_status, validate_request_body


# ============================================================
# HELPER: Standard API Response
# ============================================================

def api_response(
    success,
    message,
    data=None,
    status_code=status.HTTP_200_OK
):
    body = {
        "success":     success,
        "message":     message,
        "status_code": status_code,
    }
    if data is not None:
        body["data"] = data
    return Response(body, status=status_code)


# ============================================================
# NLP VIEW 1: GET DOCUMENT FOR NLP PROCESSING
# GET /api/v1/nlp/documents/{id}/
# ============================================================

class NLPDocumentFetchView(APIView):
    """Fetch document details for NLP processing."""

    parser_classes = [JSONParser]

    def get(self, request, pk):

        document  = get_object_or_404(Document, pk=pk)

        file_url  = None
        file_path = None

        if document.file:
            file_url  = request.build_absolute_uri(document.file.url)
            file_path = document.file.path

        return api_response(
            success=True,
            message=(
                f"Document '{document.file_name}' fetched. "
                f"Ready for NLP processing."
            ),
            data={
                "id":                document.id,
                "file_name":         document.file_name,
                "file_url":          file_url,
                "file_path":         file_path,
                "contract_type":     document.contract_type,
                "counterparty_name": document.counterparty_name,
                "governing_law":     document.governing_law,
                "status":            document.status,
                "uploaded_at":       document.uploaded_at,
                "processing_instructions": {
                    "step_1": "Read PDF from file_path using PyMuPDF",
                    "step_2": "Extract text page by page",
                    "step_3": "Run spaCy NLP processing",
                    "step_4": (
                        "POST all results to "
                        "/api/v1/nlp/documents/{id}/process/"
                    ),
                }
            }
        )


# ============================================================
# NLP VIEW 2: GET PENDING DOCUMENTS
# GET /api/v1/nlp/documents/pending/
# ============================================================

class NLPPendingDocumentsView(APIView):
    """Get all documents waiting for NLP processing."""

    parser_classes = [JSONParser]

    def get(self, request):

        pending = Document.objects.filter(
            status='uploaded'
        ).order_by('uploaded_at')

        documents_data = []
        for doc in pending:
            file_url  = None
            file_path = None
            if doc.file:
                file_url  = request.build_absolute_uri(doc.file.url)
                file_path = doc.file.path

            documents_data.append({
                "id":          doc.id,
                "file_name":   doc.file_name,
                "file_url":    file_url,
                "file_path":   file_path,
                "uploaded_at": doc.uploaded_at,
                "status":      doc.status,
            })

        return api_response(
            success=True,
            message=(
                f"{len(documents_data)} document(s) "
                f"pending NLP processing."
            ),
            data={
                "count":     len(documents_data),
                "documents": documents_data,
            }
        )


# ============================================================
# NLP VIEW 3: SUBMIT NLP RESULTS
# POST /api/v1/nlp/documents/{id}/process/
# ============================================================

class NLPProcessResultView(APIView):
    """Submit complete NLP results in one call."""

    parser_classes = [JSONParser]

    def post(self, request, pk):

        validate_request_body(request.data)
        document = get_object_or_404(Document, pk=pk)

        
        # Block re-processing of completed documents
        if document.status == 'completed':
            raise DocumentAlreadyProcessedException(
                detail=(
                    f"Document '{document.file_name}' has already been "
                    f"processed and marked as completed. "
                    f"Use PATCH /api/v1/documents/{document.id}/update-status/ "
                    f"to make changes."
                )
            )

        new_status   = request.data.get('status', 'completed')
        risk_score   = request.data.get('risk_score', 0)
        metadata     = request.data.get('metadata', {})
        clauses_data = request.data.get('clauses', [])
        risks_data   = request.data.get('risk_flags', [])

        validate_document_status(new_status)

        # Enforce same bulk limit as standalone clause/risk
        # endpoints (Day 17), so NLP submissions can't bypass
        # the protection against oversized payloads.
        MAX_BULK_ITEMS = 100

        if len(clauses_data) > MAX_BULK_ITEMS:
            return api_response(
                success=False,
                message=(
                    f"Too many clauses ({len(clauses_data)}). "
                    f"Maximum {MAX_BULK_ITEMS} per request."
                ),
                status_code=status.HTTP_400_BAD_REQUEST
            )

        if len(risks_data) > MAX_BULK_ITEMS:
            return api_response(
                success=False,
                message=(
                    f"Too many risk flags ({len(risks_data)}). "
                    f"Maximum {MAX_BULK_ITEMS} per request."
                ),
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():

                document.status     = new_status
                document.risk_score = risk_score

                if metadata.get('counterparty_name'):
                    document.counterparty_name = (
                        metadata['counterparty_name']
                    )
                if metadata.get('governing_law'):
                    document.governing_law = metadata['governing_law']
                if metadata.get('contract_start_date'):
                    document.contract_start_date = (
                        metadata['contract_start_date']
                    )
                if metadata.get('contract_end_date'):
                    document.contract_end_date = (
                        metadata['contract_end_date']
                    )

                document.save()

                saved_clauses = []
                clause_errors = []

                for i, clause_data in enumerate(clauses_data):
                    clause_data['document'] = document.id
                    s = ExtractedClauseSerializer(data=clause_data)
                    if s.is_valid():
                        s.save()
                        saved_clauses.append(s.data)
                    else:
                        clause_errors.append({"index": i, "errors": s.errors})

                saved_risks = []
                risk_errors = []

                for i, risk_data in enumerate(risks_data):
                    risk_data['document'] = document.id
                    s = RiskFlagSerializer(data=risk_data)
                    if s.is_valid():
                        s.save()
                        saved_risks.append(s.data)
                    else:
                        risk_errors.append({"index": i, "errors": s.errors})

        except DatabaseError:
            raise DatabaseOperationException()

        all_errors = clause_errors + risk_errors

        if all_errors:
            return api_response(
                success=False,
                message=(
                    f"Partial save: {len(saved_clauses)} clauses, "
                    f"{len(saved_risks)} risks saved. "
                    f"{len(all_errors)} item(s) failed."
                ),
                data={
                    "document_id":   document.id,
                    "status":        document.status,
                    "saved_clauses": saved_clauses,
                    "saved_risks":   saved_risks,
                    "errors":        all_errors,
                },
                status_code=status.HTTP_207_MULTI_STATUS
            )

        return api_response(
            success=True,
            message=(
                f"NLP results saved. "
                f"{len(saved_clauses)} clause(s) and "
                f"{len(saved_risks)} risk(s) stored."
            ),
            data={
                "document_id":   document.id,
                "file_name":     document.file_name,
                "status":        document.status,
                "risk_score":    document.risk_score,
                "total_clauses": len(saved_clauses),
                "total_risks":   len(saved_risks),
                "clauses":       saved_clauses,
                "risk_flags":    saved_risks,
            },
            status_code=status.HTTP_201_CREATED
        )


# ============================================================
# NLP VIEW 4: UPDATE STATUS ONLY
# PATCH /api/v1/nlp/documents/{id}/status/
# ============================================================

class NLPStatusUpdateView(APIView):
    """Update document status only."""

    parser_classes = [JSONParser]

    def patch(self, request, pk):

        validate_request_body(request.data)
        document   = get_object_or_404(Document, pk=pk)
        new_status = request.data.get('status', None)

        if not new_status:
            return api_response(
                success=False,
                message="Please provide 'status' in request body.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        validate_document_status(new_status)

        old_status      = document.status
        document.status = new_status
        document.save()

        return api_response(
            success=True,
            message=(
                f"Status updated: "
                f"'{old_status}' → '{new_status}'."
            ),
            data={
                "document_id": document.id,
                "file_name":   document.file_name,
                "old_status":  old_status,
                "new_status":  document.status,
            }
        )


# ============================================================
# NLP VIEW 5: GET NLP RESULTS
# GET /api/v1/nlp/documents/{id}/results/
# ============================================================

class NLPResultsView(APIView):
    """Get all NLP results for a document."""

    parser_classes = [JSONParser]

    def get(self, request, pk):

        document = get_object_or_404(Document, pk=pk)

        # WHY select_related is NOT needed here even though we
        # filter by document: clauses/risks already HAVE document
        # in memory (we just fetched it above) — select_related
        # would only help if we were accessing clause.document.*
        # somewhere below, which we are not. No change needed
        # for THESE two lines; verified during Day 29 audit.
        clauses  = ExtractedClause.objects.filter(document=document)
        risks    = RiskFlag.objects.filter(document=document)

        # Group clauses by type.
        # WHY this loop doesn't cause N+1: ExtractedClauseSerializer
        # only reads fields that already live on the `clause` row
        # itself (clause_type, clause_text, page_number,
        # confidence_score) — it never touches clause.document.*,
        # so no extra query is triggered per iteration. Verified
        # with assertNumQueries in test_query_optimization.py.
        clauses_by_type = {}
        for clause in clauses:
            ct = clause.clause_type
            if ct not in clauses_by_type:
                clauses_by_type[ct] = []
            clauses_by_type[ct].append(
                ExtractedClauseSerializer(clause).data
            )

        risks_by_severity = {"high": [], "medium": [], "low": []}
        for risk in risks:
            risks_by_severity[risk.severity].append(
                RiskFlagSerializer(risk).data
            )

        return api_response(
            success=True,
            message=(
                f"NLP results for '{document.file_name}' "
                f"retrieved successfully."
            ),
            data={
                "document_id":  document.id,
                "file_name":    document.file_name,
                "status":       document.status,
                "risk_score":   document.risk_score,
                "clauses": {
                    "total":   clauses.count(),
                    "by_type": clauses_by_type,
                },
                "risk_flags": {
                    "total":       risks.count(),
                    "by_severity": risks_by_severity,
                    "unresolved":  risks.filter(is_resolved=False).count(),
                    "resolved":    risks.filter(is_resolved=True).count(),
                },
            }
        )