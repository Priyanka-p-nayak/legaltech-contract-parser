from rest_framework import serializers
from .models import Document, ExtractedClause, RiskFlag


# ============================================================
# EXTRACTED CLAUSE SERIALIZER
# ============================================================

class ExtractedClauseSerializer(serializers.ModelSerializer):
    """
    Serializer for ExtractedClause model.
    """
    class Meta:
        model = ExtractedClause
        fields = [
            'id', 'document', 'clause_type', 'clause_text', 
            'page_number', 'confidence_score', 'extracted_at',
        ]
        read_only_fields = ['id', 'extracted_at']

    def validate_confidence_score(self, value):
        if value < 0.0 or value > 1.0:
            raise serializers.ValidationError("Confidence score must be between 0.0 and 1.0")
        return value

    def validate_page_number(self, value):
        if value < 1:
            raise serializers.ValidationError("Page number must be 1 or greater")
        return value


# ============================================================
# RISK FLAG SERIALIZER
# ============================================================

class RiskFlagSerializer(serializers.ModelSerializer):
    """
    Serializer for RiskFlag model.
    """
    class Meta:
        model = RiskFlag
        fields = [
            'id', 'document', 'risk_title', 'flagged_text', 'keyword_matched', 
            'severity', 'page_number', 'explanation', 'is_resolved', 'flagged_at',
        ]
        read_only_fields = ['id', 'flagged_at']

    def validate_severity(self, value):
        allowed = ['low', 'medium', 'high']
        if value not in allowed:
            raise serializers.ValidationError(f"Severity must be one of: {', '.join(allowed)}")
        return value

    def validate_page_number(self, value):
        if value < 1:
            raise serializers.ValidationError("Page number must be 1 or greater")
        return value


# ============================================================
# DOCUMENT LIST SERIALIZER (Lightweight)
# ============================================================

class DocumentListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for document list view.
    """
    total_clauses = serializers.SerializerMethodField()
    total_risks = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'file_name', 'contract_type', 'counterparty_name', 'governing_law', 
            'status', 'risk_score', 'file_size', 'file_size_display', 'total_clauses', 
            'total_risks', 'uploaded_at', 'updated_at',
        ]
        read_only_fields = ['id', 'file_name', 'file_size', 'uploaded_at', 'updated_at']

    def get_total_clauses(self, obj):
        return obj.clauses.count()

    def get_total_risks(self, obj):
        return obj.risk_flags.count()

    def get_file_size_display(self, obj):
        size = obj.file_size
        if size == 0: return "0 B"
        elif size < 1024: return f"{size} B"
        elif size < 1024 * 1024: return f"{size / 1024:.1f} KB"
        else: return f"{size / (1024 * 1024):.1f} MB"


# ============================================================
# DOCUMENT DETAIL SERIALIZER (Full details with nested data)
# ============================================================

class DocumentDetailSerializer(serializers.ModelSerializer):
    """
    Full detail serializer for a single document.
    """
    clauses = ExtractedClauseSerializer(many=True, read_only=True)
    risk_flags = RiskFlagSerializer(many=True, read_only=True)
    total_clauses = serializers.SerializerMethodField()
    total_risks = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'file_name', 'file', 'contract_type', 'counterparty_name', 'governing_law', 
            'contract_start_date', 'contract_end_date', 'status', 'risk_score', 'file_size', 
            'file_size_display', 'total_clauses', 'total_risks', 'uploaded_at', 'updated_at', 
            'clauses', 'risk_flags',
        ]
        read_only_fields = ['id', 'file_name', 'file_size', 'uploaded_at', 'updated_at']

    def get_total_clauses(self, obj):
        return obj.clauses.count()

    def get_total_risks(self, obj):
        return obj.risk_flags.count()

    def get_file_size_display(self, obj):
        size = obj.file_size
        if size == 0: return "0 B"
        elif size < 1024: return f"{size} B"
        elif size < 1024 * 1024: return f"{size / 1024:.1f} KB"
        else: return f"{size / (1024 * 1024):.1f} MB"


# ============================================================
# DOCUMENT UPLOAD SERIALIZER
# ============================================================

class DocumentUploadSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for PDF upload endpoint.
    """
    class Meta:
        model = Document
        fields = ['id', 'file', 'contract_type', 'counterparty_name']
        read_only_fields = ['id']

    def validate_file(self, value):
        if not value.name.endswith('.pdf'):
            raise serializers.ValidationError("Only PDF files are allowed. Please upload a .pdf file.")
        
        max_size = 10 * 1024 * 1024  # 10 MB in bytes
        if value.size > max_size:
            raise serializers.ValidationError("File size cannot exceed 10MB. Please upload a smaller file.")
        
        return value


# ============================================================
# DOCUMENT STATUS UPDATE SERIALIZER
# ============================================================

class DocumentStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating document processing status.
    """
    class Meta:
        model = Document
        fields = [
            'id', 'status', 'risk_score', 'counterparty_name', 'governing_law', 
            'contract_start_date', 'contract_end_date',
        ]
        read_only_fields = ['id']

    def validate_risk_score(self, value):
        if value < 0:
            raise serializers.ValidationError("Risk score cannot be negative")
        return value