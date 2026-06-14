from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from django.shortcuts import get_object_or_404
from django.db import DatabaseError, transaction

from .models import Document, ExtractedClause, RiskFlag
from .serializers import (
    ExtractedClauseSerializer,
    RiskFlagSerializer,
)
from .validators import validate_request_body
from .exceptions import DatabaseOperationException


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

        if document.status == 'completed':
            return api_response(
                success=False,
                message=(
                    f"Document '{document.file_name}' is already processed. "
                    f"Cannot re-process."
                ),
                status_code=status.HTTP_400_BAD_REQUEST
            )

        new_status   = request.data.get('status', 'completed')
        risk_score   = request.data.get('risk_score', 0)
        metadata     = request.data.get('metadata', {})
        clauses_data = request.data.get('clauses', [])
        risks_data   = request.data.get('risk_flags', [])

        from .validators import validate_document_status
        validate_document_status(new_status)

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

        from .validators import validate_document_status
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
        clauses  = ExtractedClause.objects.filter(document=document)
        risks    = RiskFlag.objects.filter(document=document)

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