"""
models.py
=========
Database models for the LegalTech Contract Parser.

Defines the 3 core tables: Document, ExtractedClause, and
RiskFlag. Document is the parent — ExtractedClause and
RiskFlag are independent children linked via ForeignKey
with CASCADE delete (see docs/DATABASE_MODELS.md for the
full ER diagram and design rationale).

Called by: serializers.py, views.py, nlp_views.py, admin.py
"""





from django.db import models


# ============================================================
# DOCUMENT MODEL
# ============================================================

class DocumentManager(models.Manager):
    """
    Custom manager for Document model.
    Provides helpful query methods.
    """

    def pending(self):
        """Return all documents waiting for NLP processing."""
        return self.filter(status='uploaded').order_by('uploaded_at')

    def completed(self):
        """Return all fully processed documents."""
        return self.filter(status='completed')

    def with_high_risk(self):
        """Return documents that have at least one high risk."""
        return self.filter(
            risk_flags__severity='high'
        ).distinct()

    def by_contract_type(self, contract_type):
        """Return documents of a specific contract type."""
        return self.filter(
            contract_type__icontains=contract_type
        )


class Document(models.Model):
    """
    Represents a legal contract PDF uploaded by the user.
    This is the MAIN model — all other models link to this.
    """

    STATUS_CHOICES = [
        ('uploaded',   'Uploaded'),
        ('processing', 'Processing'),
        ('completed',  'Completed'),
        ('failed',     'Failed'),
    ]

    # ── File Information ───────────────────────────────────
    file_name = models.CharField(
        max_length  = 255,
        help_text   = "Original name of the uploaded PDF file"
    )

    file = models.FileField(
        upload_to = 'contracts/',
        blank     = True,
        null      = True,
        help_text = "Uploaded PDF file"
    )

    file_size = models.PositiveIntegerField(
        default   = 0,
        help_text = "File size in bytes"
    )

    # ── Contract Metadata ──────────────────────────────────
    counterparty_name = models.CharField(
        max_length = 255,
        blank      = True,
        null       = True,
        help_text  = "Name of the other party in the contract"
    )

    contract_type = models.CharField(
        max_length = 100,
        blank      = True,
        null       = True,
        help_text  = "Type of contract e.g. NDA, MSA, Employment"
    )

    governing_law = models.CharField(
        max_length = 255,
        blank      = True,
        null       = True,
        help_text  = "Governing law jurisdiction"
    )

    contract_start_date = models.DateField(
        blank     = True,
        null      = True,
        help_text = "Contract start date"
    )

    contract_end_date = models.DateField(
        blank     = True,
        null      = True,
        help_text = "Contract end date"
    )

    # ── Processing Status ──────────────────────────────────
    status = models.CharField(
        max_length = 20,
        choices    = STATUS_CHOICES,
        default    = 'uploaded',
        db_index   = True,    # Add index for faster filtering
        help_text  = "Current processing status"
    )

    risk_score = models.IntegerField(
        default   = 0,
        help_text = "Number of high-risk clauses found"
    )

    # ── Timestamps ─────────────────────────────────────────
    uploaded_at = models.DateTimeField(
        auto_now_add = True,
        db_index     = True,   # Add index for faster ordering
        help_text    = "When the document was uploaded"
    )

    updated_at = models.DateTimeField(
        auto_now  = True,
        help_text = "When the document was last updated"
    )

    # ── Custom Manager ─────────────────────────────────────
    objects = DocumentManager()

    # ─ Meta ───────────────────────────────────────────────
    class Meta:
        ordering         = ['-uploaded_at']
        verbose_name     = 'Document'
        verbose_name_plural = 'Documents'
        indexes          = [
            models.Index(fields=['status']),
            models.Index(fields=['-uploaded_at']),
            models.Index(fields=['contract_type']),
        ]

    def __str__(self):
        return f"{self.file_name} ({self.status})"

    def save(self, *args, **kwargs):
        """
        Auto-set file_name and file_size on save.

        WHY: We calculate file_size ONCE here, at write time,
        instead of reading it from storage on every API request
        that needs it (list view, dashboard, etc.). This avoids
        a filesystem/storage hit per document on every read —
        important for the response-time targets verified in
        test_performance.py.
        """
        if self.file:
            self.file_name = self.file.name.split('/')[-1]
            try:
                self.file_size = self.file.size
            except Exception:
                self.file_size = 0
        super().save(*args, **kwargs)

    # ── Helper Properties ──────────────────────────────────

    @property
    def is_processed(self):
        """Return True if document has been processed."""
        return self.status == 'completed'

    @property
    def is_pending(self):
        """Return True if document is waiting for NLP."""
        return self.status == 'uploaded'

    @property
    def file_size_display(self):
        """Return human-readable file size."""
        size = self.file_size
        if size == 0:
            return "0 B"
        elif size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"

    @property
    def high_risk_count(self):
        """Return count of high severity risks."""
        return self.risk_flags.filter(severity='high').count()

    @property
    def unresolved_risk_count(self):
        """Return count of unresolved risk flags."""
        return self.risk_flags.filter(is_resolved=False).count()

    @property
    def total_clauses_count(self):
        """
        Single source of truth for total clause count.

        WHY: Before Day 24, DocumentListSerializer,
        DocumentDetailSerializer, and DashboardOverviewView
        each had their own duplicate `.clauses.count()` call.
        They could silently disagree if one was changed without
        the others. See docs/BUG_FIXES_DAY24.md (Bug 1 & 2).

        PERFORMANCE NOTE (Day 29): if the caller already ran
        .prefetch_related('clauses') on the queryset this
        Document came from, `self.clauses.all()` reuses that
        cached data instead of hitting the database again.
        We deliberately use .all() + len() here (not .count())
        because .count() on some Django versions can bypass the
        prefetch cache and issue a fresh COUNT query regardless.
        len() on a prefetched manager NEVER re-queries.
        """
        return len(self.clauses.all())

    @property
    def total_risks_count(self):
        """
        Single source of truth for total risk count.

        WHY: Same reasoning as total_clauses_count above —
        see docs/BUG_FIXES_DAY24.md (Bug 1 & 2).

        PERFORMANCE NOTE (Day 29): same prefetch-cache-safe
        approach as total_clauses_count — see that docstring.
        """
        return len(self.risk_flags.all())


# ============================================================
# EXTRACTED CLAUSE MODEL
# ============================================================

class ExtractedClause(models.Model):
    """
    Represents a single clause extracted from a Document.
    Created by Member 2's NLP module.
    """

    CLAUSE_TYPE_CHOICES = [
        ('confidentiality',        'Confidentiality'),
        ('termination',            'Termination'),
        ('indemnification',        'Indemnification'),
        ('governing_law',          'Governing Law'),
        ('limitation_of_liability','Limitation of Liability'),
        ('intellectual_property',  'Intellectual Property'),
        ('dispute_resolution',     'Dispute Resolution'),
        ('payment_terms',          'Payment Terms'),
        ('warranties',             'Warranties'),
        ('force_majeure',          'Force Majeure'),
        ('other',                  'Other'),
    ]

    # ── Relationship ───────────────────────────────────────
    document = models.ForeignKey(
        Document,
        on_delete    = models.CASCADE,
        related_name = 'clauses',
        db_index     = True,
        help_text    = "The document this clause belongs to"
    )

    # ── Clause Information ─────────────────────────────────
    clause_type = models.CharField(
        max_length = 50,
        choices    = CLAUSE_TYPE_CHOICES,
        default    = 'other',
        db_index   = True,
        help_text  = "Category of this legal clause"
    )

    clause_text = models.TextField(
        help_text = "The full text of the extracted clause"
    )

    page_number = models.PositiveIntegerField(
        default   = 1,
        help_text = "Page number in the PDF"
    )

    confidence_score = models.FloatField(
        default   = 0.0,
        help_text = "NLP confidence score 0.0 to 1.0"
    )

    # ── Timestamp ──────────────────────────────────────────
    extracted_at = models.DateTimeField(
        auto_now_add = True,
        help_text    = "When this clause was extracted"
    )

    class Meta:
        ordering         = ['page_number']
        verbose_name     = 'Extracted Clause'
        verbose_name_plural = 'Extracted Clauses'
        indexes          = [
            models.Index(fields=['document', 'clause_type']),
            models.Index(fields=['clause_type']),
        ]

    def __str__(self):
        return (
            f"{self.clause_type} — "
            f"Page {self.page_number} "
            f"({self.document.file_name})"
        )


# ============================================================
# RISK FLAG MODEL
# ============================================================

class RiskFlag(models.Model):
    """
    Represents a high-risk finding in a Document.
    Created by Member 2's NLP module.
    """

    SEVERITY_CHOICES = [
        ('low',    'Low'),
        ('medium', 'Medium'),
        ('high',   'High'),
    ]

    # ── Relationship ───────────────────────────────────────
    document = models.ForeignKey(
        Document,
        on_delete    = models.CASCADE,
        related_name = 'risk_flags',
        db_index     = True,
        help_text    = "The document this risk belongs to"
    )

    # ── Risk Information ──────────────────────────────────
    risk_title = models.CharField(
        max_length = 255,
        help_text  = "Short title of the risk"
    )

    flagged_text = models.TextField(
        help_text = "The exact text that was flagged"
    )

    keyword_matched = models.CharField(
        max_length = 100,
        blank      = True,
        null       = True,
        help_text  = "The keyword that triggered this flag"
    )

    severity = models.CharField(
        max_length = 10,
        choices    = SEVERITY_CHOICES,
        default    = 'medium',
        db_index   = True,
        help_text  = "Severity level"
    )

    page_number = models.PositiveIntegerField(
        default   = 1,
        help_text = "Page number in the PDF"
    )

    explanation = models.TextField(
        blank     = True,
        null      = True,
        help_text = "Why this clause is risky"
    )

    is_resolved = models.BooleanField(
        default   = False,
        db_index  = True,
        help_text = "Whether this risk has been reviewed"
    )

    # ── Timestamp ──────────────────────────────────────────
    flagged_at = models.DateTimeField(
        auto_now_add = True,
        help_text    = "When this risk was flagged"
    )

    class Meta:
        ordering         = ['-severity', 'page_number']
        verbose_name     = 'Risk Flag'
        verbose_name_plural = 'Risk Flags'
        indexes          = [
            models.Index(fields=['document', 'severity']),
            models.Index(fields=['severity']),
            models.Index(fields=['is_resolved']),
        ]

    def __str__(self):
        return (
            f"[{self.severity.upper()}] "
            f"{self.risk_title} — "
            f"{self.document.file_name}"
        )