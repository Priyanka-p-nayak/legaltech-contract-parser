"""
serializers.py
==============
DRF serializers that convert between Document/ExtractedClause/
RiskFlag model instances and JSON for the API layer.

Six serializers total:
  - ExtractedClauseSerializer, RiskFlagSerializer (used both
    standalone and nested inside DocumentDetailSerializer)
  - DocumentListSerializer   — lightweight, used in list views
  - DocumentDetailSerializer — full, includes nested clauses/risks
  - DocumentUploadSerializer — accepts only upload-relevant fields
  - DocumentStatusUpdateSerializer — accepts only updatable fields

Called by: views.py, nlp_views.py
"""

from rest_framework import serializers

from .models import Document, ExtractedClause, RiskFlag


# ============================================================
# EXTRACTED CLAUSE SERIALIZER
# ============================================================

class ExtractedClauseSerializer(serializers.ModelSerializer):
    """Serializer for ExtractedClause model."""

    class Meta:
        model = ExtractedClause
        fields = [
            'id',
            'document',
            'clause_type',
            'clause_text',
            'page_number',
            'confidence_score',
            'extracted_at',
        ]
        read_only_fields = ['id', 'extracted_at']

    def validate_confidence_score(self, value):
        """Confidence score must be between 0.0 and 1.0"""
        if value < 0.0 or value > 1.0:
            raise serializers.ValidationError(
                "Confidence score must be between 0.0 and 1.0"
            )
        return round(value, 4)

    def validate_page_number(self, value):
        """Page number must be >= 1"""
        if value < 1:
            raise serializers.ValidationError(
                "Page number must be 1 or greater"
            )
        return value

    def validate_clause_text(self, value):
        """
        Clause text must not be empty and meet a minimum length.

        WHY 10 characters minimum: this rejects obviously broken
        NLP extractions (e.g. a stray "N/A" or single word caught
        by a bad regex match) without being so strict that it
        rejects legitimate short clauses. See test_edge_cases.py
        for the exact boundary tests (9 chars rejected, 10 accepted).
        """
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "Clause text cannot be empty"
            )
        if len(value) < 10:
            raise serializers.ValidationError(
                "Clause text is too short. "
                "Minimum 10 characters required."
            )
        if len(value) > 50000:
            raise serializers.ValidationError(
                "Clause text is too long. "
                "Maximum 50000 characters allowed."
            )
        return value

    def validate_clause_type(self, value):
        """Clause type must be one of the allowed values"""
        allowed = [
            'confidentiality',
            'termination',
            'indemnification',
            'governing_law',
            'limitation_of_liability',
            'intellectual_property',
            'dispute_resolution',
            'payment_terms',
            'warranties',
            'force_majeure',
            'other',
        ]
        if value not in allowed:
            raise serializers.ValidationError(
                f"'{value}' is not valid. "
                f"Allowed types: {', '.join(allowed)}"
            )
        return value


# ============================================================
# RISK FLAG SERIALIZER
# ============================================================

class RiskFlagSerializer(serializers.ModelSerializer):
    """Serializer for RiskFlag model."""

    class Meta:
        model = RiskFlag
        fields = [
            'id',
            'document',
            'risk_title',
            'flagged_text',
            'keyword_matched',
            'severity',
            'page_number',
            'explanation',
            'is_resolved',
            'flagged_at',
        ]
        read_only_fields = ['id', 'flagged_at']

    def validate_severity(self, value):
        """Severity must be low, medium, or high"""
        allowed = ['low', 'medium', 'high']
        if value not in allowed:
            raise serializers.ValidationError(
                f"Severity must be one of: "
                f"{', '.join(allowed)}"
            )
        return value

    def validate_page_number(self, value):
        """Page number must be >= 1"""
        if value < 1:
            raise serializers.ValidationError(
                "Page number must be 1 or greater"
            )
        return value

    def validate_risk_title(self, value):
        """Risk title must not be empty"""
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "Risk title cannot be empty"
            )
        return value

    def validate_flagged_text(self, value):
        """Flagged text must not be empty"""
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "Flagged text cannot be empty"
            )
        return value


# ============================================================
# DOCUMENT LIST SERIALIZER
# ============================================================

class DocumentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for document list."""

    total_clauses = serializers.SerializerMethodField()
    total_risks = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id',
            'file_name',
            'contract_type',
            'counterparty_name',
            'governing_law',
            'status',
            'risk_score',
            'file_size',
            'file_size_display',
            'total_clauses',
            'total_risks',
            'uploaded_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'file_name',
            'file_size',
            'uploaded_at',
            'updated_at',
        ]

    def get_total_clauses(self, obj):
        """
        Return clause count without N+1 queries.
        
        WHY: Check for annotated 'clause_count' attribute first
        (added by views.py's annotate() call). Only fall back to
        model property if annotation isn't present.
        """
        # Check if annotation exists (from views.py)
        if hasattr(obj, 'clause_count'):
            return obj.clause_count
        # Fallback to model property (for non-list views)
        return obj.total_clauses_count

    def get_total_risks(self, obj):
        """
        Return risk count without N+1 queries.
        
        WHY: Check for annotated 'risk_count' attribute first
        (added by views.py's annotate() call). Only fall back to
        model property if annotation isn't present.
        """
        # Check if annotation exists (from views.py)
        if hasattr(obj, 'risk_count'):
            return obj.risk_count
        # Fallback to model property (for non-list views)
        return obj.total_risks_count

    def get_file_size_display(self, obj):
        size = obj.file_size
        if size == 0:
            return "0 B"
        elif size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"

# ============================================================
# DOCUMENT DETAIL SERIALIZER
# ============================================================

class DocumentDetailSerializer(serializers.ModelSerializer):
    """Full serializer for one document."""

    clauses = ExtractedClauseSerializer(many=True, read_only=True)
    risk_flags = RiskFlagSerializer(many=True, read_only=True)
    total_clauses = serializers.SerializerMethodField()
    total_risks = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id',
            'file_name',
            'file',
            'contract_type',
            'counterparty_name',
            'governing_law',
            'contract_start_date',
            'contract_end_date',
            'status',
            'risk_score',
            'file_size',
            'file_size_display',
            'total_clauses',
            'total_risks',
            'uploaded_at',
            'updated_at',
            'clauses',
            'risk_flags',
        ]
        read_only_fields = [
            'id',
            'file_name',
            'file_size',
            'uploaded_at',
            'updated_at',
        ]

    def get_total_clauses(self, obj):
        return obj.total_clauses_count

    def get_total_risks(self, obj):
        return obj.total_risks_count

    def get_file_size_display(self, obj):
        size = obj.file_size
        if size == 0:
            return "0 B"
        elif size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"


# ============================================================
# DOCUMENT UPLOAD SERIALIZER
# ============================================================

class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for PDF upload endpoint."""

    class Meta:
        model = Document
        fields = [
            'id',
            'file',
            'contract_type',
            'counterparty_name',
        ]
        read_only_fields = ['id']

    def validate_file(self, value):
        """Validate uploaded file."""
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError(
                "Only PDF files are allowed. "
                "Please upload a .pdf file."
            )

        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                "File size cannot exceed 10MB."
            )

        return value

    def validate_contract_type(self, value):
        """Strip whitespace from contract type"""
        if value:
            return value.strip()
        return value

    def validate_counterparty_name(self, value):
        """Strip whitespace from counterparty name"""
        if value:
            return value.strip()
        return value


# ============================================================
# DOCUMENT STATUS UPDATE SERIALIZER
# ============================================================

class DocumentStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating document status."""

    class Meta:
        model = Document
        fields = [
            'id',
            'status',
            'risk_score',
            'counterparty_name',
            'governing_law',
            'contract_start_date',
            'contract_end_date',
        ]
        read_only_fields = ['id']

    def validate_risk_score(self, value):
        """Risk score cannot be negative"""
        if value < 0:
            raise serializers.ValidationError(
                "Risk score cannot be negative"
            )
        return value

    def validate_status(self, value):
        """Status must be one of allowed values"""
        allowed = ['uploaded', 'processing', 'completed', 'failed']
        if value not in allowed:
            raise serializers.ValidationError(
                f"'{value}' is not valid. "
                f"Allowed: {', '.join(allowed)}"
            )
        return value

    def validate_counterparty_name(self, value):
        """Strip whitespace"""
        if value:
            return value.strip()
        return value

    def validate_governing_law(self, value):
        """Strip whitespace"""
        if value:
            return value.strip()
        return value