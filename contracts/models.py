from django.db import models

# ============================================================
# DOCUMENT MODEL
# Represents a legal contract PDF uploaded by the user.
# This is the MAIN model - everything else links to this.
# ============================================================

class Document(models.Model):

    # Status choices for the document processing pipeline
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    # ── Basic Information ──────────────────────────────────

    file_name = models.CharField(
        max_length=255,
        help_text="Original name of the uploaded PDF file"
    )

    file = models.FileField(
        upload_to='contracts/',
        help_text="Uploaded PDF file"
    )

    file_size = models.PositiveIntegerField(
        default=0,
        help_text="File size in bytes"
    )

    # ── Contract Metadata ──────────────────────────────────

    counterparty_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Name of the other party in the contract"
    )

    contract_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Type of contract e.g. NDA, MSA, Employment"
    )

    governing_law = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Governing law jurisdiction e.g. California, India"
    )

    contract_start_date = models.DateField(
        blank=True,
        null=True,
        help_text="Contract start date"
    )

    contract_end_date = models.DateField(
        blank=True,
        null=True,
        help_text="Contract end date"
    )

    # ── Processing Status ──────────────────────────────────

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='uploaded',
        help_text="Current processing status of the document"
    )

    risk_score = models.IntegerField(
        default=0,
        help_text="Number of high-risk clauses found in the document"
    )

    # ── Timestamps ─────────────────────────────────────────

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the document was uploaded"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the document record was last updated"
    )

    # ── Meta Configuration ─────────────────────────────────

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'

    def __str__(self):
        return f"{self.file_name} ({self.status})"

    # ── Custom Save Method ─────────────────────────────────

    def save(self, *args, **kwargs):
        """
        Override save to automatically:
        1. Set file_name from the uploaded file
        2. Calculate and store file size
        """
        if self.file:
            self.file_name = self.file.name.split('/')[-1]

            try:
                self.file_size = self.file.size
            except Exception:
                self.file_size = 0

        super().save(*args, **kwargs)


# ============================================================
# EXTRACTED CLAUSE MODEL
# Represents a single clause extracted from a Document.
# ============================================================

class ExtractedClause(models.Model):

    CLAUSE_TYPE_CHOICES = [
        ('confidentiality', 'Confidentiality'),
        ('termination', 'Termination'),
        ('indemnification', 'Indemnification'),
        ('governing_law', 'Governing Law'),
        ('limitation_of_liability', 'Limitation of Liability'),
        ('intellectual_property', 'Intellectual Property'),
        ('dispute_resolution', 'Dispute Resolution'),
        ('payment_terms', 'Payment Terms'),
        ('warranties', 'Warranties'),
        ('force_majeure', 'Force Majeure'),
        ('other', 'Other'),
    ]

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='clauses',
        help_text="The document this clause belongs to"
    )

    clause_type = models.CharField(
        max_length=50,
        choices=CLAUSE_TYPE_CHOICES,
        default='other',
        help_text="Category/type of this legal clause"
    )

    clause_text = models.TextField(
        help_text="The full text of the extracted clause"
    )

    page_number = models.PositiveIntegerField(
        default=1,
        help_text="Page number where this clause appears in the PDF"
    )

    confidence_score = models.FloatField(
        default=0.0,
        help_text="NLP confidence score between 0.0 and 1.0"
    )

    extracted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this clause was extracted"
    )

    class Meta:
        ordering = ['page_number']
        verbose_name = 'Extracted Clause'
        verbose_name_plural = 'Extracted Clauses'

    def __str__(self):
        return (
            f"{self.clause_type} — "
            f"Page {self.page_number} "
            f"({self.document.file_name})"
        )


# ============================================================
# RISK FLAG MODEL
# Represents a specific high-risk finding in a Document.
# ============================================================

class RiskFlag(models.Model):

    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='risk_flags',
        help_text="The document this risk flag belongs to"
    )

    risk_title = models.CharField(
        max_length=255,
        help_text="Short title of the risk e.g. 'Unlimited Liability Found'"
    )

    flagged_text = models.TextField(
        help_text="The exact text that was flagged as risky"
    )

    keyword_matched = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="The risk keyword that triggered this flag"
    )

    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='medium',
        help_text="Severity level of this risk"
    )

    page_number = models.PositiveIntegerField(
        default=1,
        help_text="Page number where the risk was found"
    )

    explanation = models.TextField(
        blank=True,
        null=True,
        help_text="Explanation of why this clause is considered risky"
    )

    is_resolved = models.BooleanField(
        default=False,
        help_text="Whether this risk has been reviewed and resolved"
    )

    flagged_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this risk was flagged"
    )

    class Meta:
        ordering = ['-severity', 'page_number']
        verbose_name = 'Risk Flag'
        verbose_name_plural = 'Risk Flags'

    def __str__(self):
        return (
            f"[{self.severity.upper()}] "
            f"{self.risk_title} — "
            f"{self.document.file_name}"
        )