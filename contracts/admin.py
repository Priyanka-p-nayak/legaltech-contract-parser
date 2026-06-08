from django.contrib import admin
from .models import Document

# ============================================================
# DOCUMENT ADMIN CONFIGURATION
# Controls how Document model appears in Django Admin panel
# ============================================================

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):

    # Columns shown in the document list page
    list_display = [
        'id',
        'file_name',
        'contract_type',
        'counterparty_name',
        'governing_law',
        'status',
        'risk_score',
        'file_size',
        'uploaded_at',
    ]

    # Clickable link column (clicking opens detail page)
    list_display_links = ['id', 'file_name']

    # Filter sidebar on the right side of admin list
    list_filter = [
        'status',
        'contract_type',
        'uploaded_at',
    ]

    # Search bar - search by these fields
    search_fields = [
        'file_name',
        'counterparty_name',
        'governing_law',
        'contract_type',
    ]

    # Fields that can be edited directly in the list view
    list_editable = ['status']

    # Default ordering in admin (newest first)
    ordering = ['-uploaded_at']

    # How many documents per page in admin
    list_per_page = 20

    # Organize fields into sections in the detail/edit page
    fieldsets = (
        # Section 1: File Information
        ('File Information', {
            'fields': ('file', 'file_name', 'file_size')
        }),
        # Section 2: Contract Details
        ('Contract Details', {
            'fields': (
                'contract_type',
                'counterparty_name',
                'governing_law',
                'contract_start_date',
                'contract_end_date',
            )
        }),
        # Section 3: Processing Info
        ('Processing Information', {
            'fields': ('status', 'risk_score')
        }),
        # Section 4: Timestamps (read only)
        ('Timestamps', {
            'fields': ('uploaded_at', 'updated_at'),
            'classes': ('collapse',)  # Collapsible section
        }),
    )

    # These fields are auto-set so make them read-only
    readonly_fields = ['uploaded_at', 'updated_at', 'file_size', 'file_name']