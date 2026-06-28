from django.contrib import admin
from django.utils.html import format_html
from .models import Document, ExtractedClause, RiskFlag


# ============================================================
# INLINE ADMIN FOR EXTRACTED CLAUSES
# ============================================================
class ExtractedClauseInline(admin.TabularInline):
    model = ExtractedClause
    extra = 0
    readonly_fields = ('clause_type', 'clause_text', 'page_number', 'confidence_score', 'extracted_at')
    can_delete = False


# ============================================================
# INLINE ADMIN FOR RISK FLAGS
# ============================================================
class RiskFlagInline(admin.TabularInline):
    model = RiskFlag
    extra = 0
    readonly_fields = ('risk_title', 'severity', 'flagged_text', 'page_number', 'is_resolved', 'flagged_at')
    can_delete = False


# ============================================================
# DOCUMENT ADMIN
# ============================================================
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'file_name',
        'file_size',
        'contract_type',
        'counterparty_name',
        'governing_law',
        'status',           # ← FIXED: Added status
        'risk_score',
        'uploaded_at',
    ]
    
    list_display_links = ['id', 'file_name']
    
    list_filter = [
        'status',
        'contract_type',
        'uploaded_at',
    ]
    
    search_fields = [
        'file_name',
        'counterparty_name',
        'governing_law',
        'contract_type',
    ]
    
    list_editable = ['status']  # Now valid because status is in list_display
    
    ordering = ['-uploaded_at']
    list_per_page = 20
    
    fieldsets = (
        ('File Information', {
            'fields': ('file', 'file_name', 'file_size')
        }),
        ('Contract Details', {
            'fields': (
                'contract_type',
                'counterparty_name',
                'governing_law',
                'contract_start_date',
                'contract_end_date',
            )
        }),
        ('Processing Information', {
            'fields': ('status', 'risk_score')
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['uploaded_at', 'updated_at', 'file_size', 'file_name']
    inlines = [ExtractedClauseInline, RiskFlagInline]


# ============================================================
# EXTRACTED CLAUSE ADMIN
# ============================================================
@admin.register(ExtractedClause)
class ExtractedClauseAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'document',
        'clause_type',
        'page_number',
        'confidence_score',
        'extracted_at',
    ]
    
    list_display_links = ['id', 'document']
    
    list_filter = [
        'clause_type',
        'extracted_at',
    ]
    
    search_fields = [
        'clause_text',
        'document__file_name',
    ]
    
    ordering = ['document', 'page_number']
    list_per_page = 25
    
    fieldsets = (
        ('Document', {
            'fields': ('document',)
        }),
        ('Clause Details', {
            'fields': (
                'clause_type',
                'clause_text',
                'page_number',
                'confidence_score',
            )
        }),
        ('Timestamp', {
            'fields': ('extracted_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['extracted_at']


# ============================================================
# RISK FLAG ADMIN
# ============================================================
@admin.register(RiskFlag)
class RiskFlagAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'document',
        'risk_title',
        'flagged_text',
        'keyword_matched',
        'severity',
        'page_number',
        'explanation',
        'is_resolved',      # ← FIXED: Added is_resolved
        'flagged_at',
    ]
    
    list_display_links = ['id', 'risk_title']
    
    list_filter = [
        'severity',
        'is_resolved',
        'flagged_at',
    ]
    
    search_fields = [
        'risk_title',
        'flagged_text',
        'keyword_matched',
        'document__file_name',
    ]
    
    list_editable = ['is_resolved']  # Now valid because is_resolved is in list_display
    
    ordering = ['-severity', 'page_number']
    list_per_page = 25
    
    fieldsets = (
        ('Document', {
            'fields': ('document',)
        }),
        ('Risk Details', {
            'fields': (
                'risk_title',
                'flagged_text',
                'keyword_matched',
                'severity',
                'page_number',
                'explanation',
            )
        }),
        ('Status', {
            'fields': ('is_resolved',)
        }),
        ('Timestamp', {
            'fields': ('flagged_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['flagged_at']