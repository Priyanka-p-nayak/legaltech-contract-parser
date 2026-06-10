from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404

from .models import Document, ExtractedClause, RiskFlag
from .serializers import (
    DocumentListSerializer,
    DocumentDetailSerializer,
    DocumentUploadSerializer,
    DocumentStatusUpdateSerializer,
    ExtractedClauseSerializer,
    RiskFlagSerializer,
)

def api_response(success, message, data=None, status_code=status.HTTP_200_OK):
    response_body = {"success": success, "message": message}
    if data is not None:
        response_body["data"] = data
    return Response(response_body, status=status_code)

class HealthCheckView(APIView):
    def get(self, request):
        return api_response(
            success=True,
            message="LegalTech API is running successfully.",
            data={
                "api_version": "1.0.0",
                "status": "healthy",
                "total_documents": Document.objects.count(),
                "total_clauses": ExtractedClause.objects.count(),
                "total_risk_flags": RiskFlag.objects.count(),
                "endpoints": {
                    "upload_document":  "POST /api/documents/upload/",
                    "list_documents":   "GET  /api/documents/",
                    "document_detail":  "GET  /api/documents/{id}/",
                    "update_status":    "PATCH /api/documents/{id}/update-status/",
                    "save_clauses":     "POST /api/documents/{id}/clauses/",
                    "get_clauses":      "GET  /api/documents/{id}/clauses/",
                    "save_risks":       "POST /api/documents/{id}/risks/",
                    "get_risks":        "GET  /api/documents/{id}/risks/",
                    "document_summary": "GET  /api/documents/{id}/summary/",
                    "stats":            "GET  /api/stats/",
                }
            }
        )

class DocumentUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        if 'file' not in request.FILES:
            return api_response(success=False, message="No file provided. Please upload a PDF file.", status_code=status.HTTP_400_BAD_REQUEST)

        serializer = DocumentUploadSerializer(data=request.data)
        if serializer.is_valid():
            document = serializer.save()
            return api_response(success=True, message="PDF uploaded successfully. Ready for processing.", data=DocumentDetailSerializer(document).data, status_code=status.HTTP_201_CREATED)

        return api_response(success=False, message="File upload failed. Please check the errors.", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

class DocumentListView(APIView):
    parser_classes = [JSONParser]

    def get(self, request):
        documents = Document.objects.all()

        # Filter: status
        status_filter = request.query_params.get('status', None)
        if status_filter:
            allowed_statuses = ['uploaded', 'processing', 'completed', 'failed']
            if status_filter not in allowed_statuses:
                return api_response(success=False, message=f"Invalid status. Allowed: {', '.join(allowed_statuses)}", status_code=status.HTTP_400_BAD_REQUEST)
            documents = documents.filter(status=status_filter)

        # Filter: contract_type
        contract_type_filter = request.query_params.get('contract_type', None)
        if contract_type_filter:
            documents = documents.filter(contract_type__icontains=contract_type_filter)

        # Search: file_name or counterparty_name
        search_query = request.query_params.get('search', None)
        if search_query:
            from django.db.models import Q
            documents = documents.filter(
                Q(file_name__icontains=search_query) |
                Q(counterparty_name__icontains=search_query)
            )

        # Ordering
        ordering = request.query_params.get('ordering', '-uploaded_at')
        allowed_orderings = ['uploaded_at', '-uploaded_at', 'risk_score', '-risk_score']
        if ordering in allowed_orderings:
            documents = documents.order_by(ordering)

        serializer = DocumentListSerializer(documents, many=True)
        return api_response(success=True, message=f"{documents.count()} document(s) found.", data={"count": documents.count(), "documents": serializer.data})

class DocumentDetailView(APIView):
    parser_classes = [JSONParser]

    def get(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        serializer = DocumentDetailSerializer(document)
        return api_response(success=True, message="Document retrieved successfully.", data=serializer.data)

class DocumentStatusUpdateView(APIView):
    parser_classes = [JSONParser]

    def patch(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        serializer = DocumentStatusUpdateSerializer(document, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(success=True, message="Document status updated successfully.", data=serializer.data)
        return api_response(success=False, message="Status update failed. Please check the errors.", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

class ExtractedClauseCreateView(APIView):
    parser_classes = [JSONParser]

    def post(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        if isinstance(request.data, list):
            saved_clauses, errors = [], []
            for index, clause_data in enumerate(request.data):
                clause_data['document'] = document.id
                serializer = ExtractedClauseSerializer(data=clause_data)
                if serializer.is_valid():
                    serializer.save()
                    saved_clauses.append(serializer.data)
                else:
                    errors.append({"index": index, "errors": serializer.errors})
            if errors:
                return api_response(success=False, message=f"{len(saved_clauses)} saved, {len(errors)} failed.", data={"saved": saved_clauses, "errors": errors}, status_code=status.HTTP_400_BAD_REQUEST)
            return api_response(success=True, message=f"{len(saved_clauses)} clause(s) saved successfully.", data=saved_clauses, status_code=status.HTTP_201_CREATED)
        else:
            data = request.data.copy()
            data['document'] = document.id
            serializer = ExtractedClauseSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return api_response(success=True, message="Clause saved successfully.", data=serializer.data, status_code=status.HTTP_201_CREATED)
            return api_response(success=False, message="Failed to save clause.", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        clause_type = request.query_params.get('clause_type', None)
        clauses = ExtractedClause.objects.filter(document=document)
        if clause_type:
            clauses = clauses.filter(clause_type__icontains=clause_type)
        serializer = ExtractedClauseSerializer(clauses, many=True)
        return api_response(success=True, message=f"{clauses.count()} clause(s) found.", data={"document_id": pk, "count": clauses.count(), "clauses": serializer.data})

class RiskFlagCreateView(APIView):
    parser_classes = [JSONParser]

    def post(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        if isinstance(request.data, list):
            saved_risks, errors = [], []
            for index, risk_data in enumerate(request.data):
                risk_data['document'] = document.id
                serializer = RiskFlagSerializer(data=risk_data)
                if serializer.is_valid():
                    serializer.save()
                    saved_risks.append(serializer.data)
                else:
                    errors.append({"index": index, "errors": serializer.errors})
            if errors:
                return api_response(success=False, message=f"{len(saved_risks)} saved, {len(errors)} failed.", data={"saved": saved_risks, "errors": errors}, status_code=status.HTTP_400_BAD_REQUEST)
            return api_response(success=True, message=f"{len(saved_risks)} risk flag(s) saved successfully.", data=saved_risks, status_code=status.HTTP_201_CREATED)
        else:
            data = request.data.copy()
            data['document'] = document.id
            serializer = RiskFlagSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return api_response(success=True, message="Risk flag saved successfully.", data=serializer.data, status_code=status.HTTP_201_CREATED)
            return api_response(success=False, message="Failed to save risk flag.", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        severity = request.query_params.get('severity', None)
        risks = RiskFlag.objects.filter(document=document)
        if severity:
            risks = risks.filter(severity=severity)
        serializer = RiskFlagSerializer(risks, many=True)
        return api_response(success=True, message=f"{risks.count()} risk flag(s) found.", data={"document_id": pk, "count": risks.count(), "risk_flags": serializer.data})

class DocumentSummaryView(APIView):
    parser_classes = [JSONParser]

    def get(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        high_risks   = document.risk_flags.filter(severity='high').count()
        medium_risks = document.risk_flags.filter(severity='medium').count()
        low_risks    = document.risk_flags.filter(severity='low').count()

        clause_breakdown = {}
        for clause in document.clauses.all():
            clause_type = clause.clause_type
            clause_breakdown[clause_type] = clause_breakdown.get(clause_type, 0) + 1

        summary = {
            "id": document.id, "file_name": document.file_name,
            "contract_type": document.contract_type, "counterparty_name": document.counterparty_name,
            "governing_law": document.governing_law, "status": document.status, "uploaded_at": document.uploaded_at,
            "risk_summary": {"total": document.risk_flags.count(), "high": high_risks, "medium": medium_risks, "low": low_risks},
            "clause_summary": {"total": document.clauses.count(), "breakdown": clause_breakdown}
        }
        return api_response(success=True, message="Document summary retrieved successfully.", data=summary)

class StatsView(APIView):
    parser_classes = [JSONParser]

    def get(self, request):
        from django.db.models import Count
        total_docs = Document.objects.count()
        total_clauses = ExtractedClause.objects.count()
        total_risks = RiskFlag.objects.count()

        status_breakdown = list(Document.objects.values('status').annotate(count=Count('id')))
        severity_breakdown = list(RiskFlag.objects.values('severity').annotate(count=Count('id')))
        type_breakdown = list(Document.objects.exclude(contract_type__isnull=True).values('contract_type').annotate(count=Count('id')))

        stats = {
            "total_documents": total_docs, "total_clauses": total_clauses, "total_risk_flags": total_risks,
            "documents_by_status": status_breakdown, "risks_by_severity": severity_breakdown, "documents_by_type": type_breakdown,
        }
        return api_response(success=True, message="Statistics retrieved successfully.", data=stats)