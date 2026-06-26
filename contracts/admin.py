from django.contrib import admin
from django.utils.html import format_html
from .models import Document, ExtractedClause, RiskFlag

# ============================================================
# INLINE ADMIN FOR EXTRACTED CLAUSES
# Shows clauses directly inside the Document detail page
# ============================================================
class ExtractedClauseInline(admin.TabularInline):
    model = ExtractedClause
    extra = 0  # Don't show empty extra rows for adding new ones
    readonly_fields = ('clause_type', 'clause_text', 'page_number', 'confidence_score', 'extracted_at')
    can_delete = False
    verbose_name = "Extracted Clause"
    verbose_name_plural = "Extracted Clauses (Read-Only)"

    def has_add_permission(self, request, obj=None):
        return False  # Prevent adding clauses manually from admin

# ============================================================
# INLINE ADMIN FOR RISK FLAGS
# Shows risk flags directly inside the Document detail page
# ============================================================
class RiskFlagInline(admin.TabularInline):
    model = RiskFlag
    extra = 0
    readonly_fields = ('risk_title', 'severity_badge', 'flagged_text', 'page_number', 'is_resolved')
    can_delete = False
    verbose_name = "Risk Flag"
    verbose_name_plural = "Risk Flags (Read-Only)"

    def has_add_permission(self, request, obj=None):
        return False

    def severity_badge(self, obj):
        """Displays a colored badge for the risk severity."""
        colors = {
            'high': '#dc3545',    # Red
            'medium': '#fd7e14',  # Orange
            'low': '#28a745',     # Green
        }
        color = colors.get(obj.severity, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold; padding: 3px 8px; border-radius: 4px; background-color: {}20;">{}</span>',
            color, color, obj.severity.upper()
        )
    severity_badge.short_description = "Severity"

# ============================================================
# DOCUMENT ADMIN (THE MAIN DASHBOARD VIEW)
# ============================================================
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    # --- List View (Dashboard Table) ---
    list_display = (
        'id', 
        'file_name_link', 
        'contract_type', 
        'counterparty_name', 
        'status_badge', 
        'risk_score', 
        'high_risk_count',
        'uploaded_at',
        'is_processed'
    )
    
    # --- Filters (Sidebar) ---
    list_filter = (
        'status', 
        'contract_type', 
        'risk_score',
        'uploaded_at',
        'governing_law'
    )
    
    # --- Search Bar ---
    search_fields = (
        'file_name', 
        'counterparty_name', 
        'governing_law',
        'contract_type'
    )
    
    # --- Date Hierarchy (Navigate by date) ---
    date_hierarchy = 'uploaded_at'
    
    # --- Ordering ---
    ordering = ('-uploaded_at',)
    
    # --- Read-only fields ---
    readonly_fields = (
        'file_name', 
        'file_size_display', 
        'uploaded_at', 
        'updated_at',
        'total_clauses_count',
        'total_risks_count',
        'dashboard_summary'
    )
    
    # --- Inlines (Show clauses and risks inside Document detail) ---
    inlines = [ExtractedClauseInline, RiskFlagInline]
    
    # --- Actions (Bulk actions) ---
    actions = ['mark_as_completed', 'mark_as_failed']

    # --- Fieldsets (Organize the detail page) ---
    fieldsets = (
        ('File Information', {
            'fields': ('file', 'file_name', 'file_size_display')
        }),
        ('Contract Details', {
            'fields': (
                'contract_type', 
                'counterparty_name', 
                'governing_law',
                'contract_start_date',
                'contract_end_date'
            )
        }),
        ('Processing & Risk Status', {
            'fields': ('status', 'risk_score', 'dashboard_summary'),
            'description': 'Update status manually if NLP processing fails or needs retry.'
        }),
        ('Statistics (Auto-calculated)', {
            'fields': ('total_clauses_count', 'total_risks_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # --- Custom Display Methods ---
    def file_name_link(self, obj):
        """Makes the file name a clickable link to the detail page."""
        return format_html('<a href="{}">{}</a>', obj.id, obj.file_name)
    file_name_link.short_description = "File Name"

    def status_badge(self, obj):
        """Displays a colored badge for the document status."""
        colors = {
            'uploaded': '#17a2b8',    # Blue/Info
            'processing': '#ffc107',  # Yellow/Warning
            'completed': '#28a745',   # Green/Success
            'failed': '#dc3545',      # Red/Danger
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold; padding: 3px 8px; border-radius: 4px; background-color: {}20;">{}</span>',
            color, color, obj.status.upper()
        )
    status_badge.short_description = "Status"

    def high_risk_count(self, obj):
        """Displays the count of high-severity risks in red."""
        count = obj.risk_flags.filter(severity='high').count()
        if count > 0:
            return format_html('<span style="color: #dc3545; font-weight: bold;">{} High</span>', count)
        return format_html('<span style="color: #28a745;">0 High</span>')
    high_risk_count.short_description = "High Risks"

    def is_processed(self, obj):
        """Displays a checkmark or cross based on processing status."""
        if obj.status == 'completed':
            return format_html('<span style="color: #28a745; font-size: 1.2em;">✔</span>')
        elif obj.status == 'failed':
            return format_html('<span style="color: #dc3545; font-size: 1.2em;">✘</span>')
        return format_html('<span style="color: #ffc107; font-size: 1.2em;">⏳</span>')
    is_processed.short_description = "Processed?"

    def dashboard_summary(self, obj):
        """Shows a quick summary of risks inside the detail page."""
        total = obj.risk_flags.count()
        high = obj.risk_flags.filter(severity='high').count()
        medium = obj.risk_flags.filter(severity='medium').count()
        low = obj.risk_flags.filter(severity='low').count()
        return format_html(
            "<b>Total Risks:</b> {} | "
            "<span style='color:red'>High: {}</span> | "
            "<span style='color:orange'>Medium: {}</span> | "
            "<span style='color:green'>Low: {}</span>",
            total, high, medium, low
        )
    dashboard_summary.short_description = "Risk Summary"

    # --- Bulk Actions ---
    @admin.action(description="Mark selected documents as Completed")
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f"{updated} documents marked as completed.")

    @admin.action(description="Mark selected documents as Failed")
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f"{updated} documents marked as failed.")