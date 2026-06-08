from django.db import models

# ============================================================
# DOCUMENT MODEL
# Represents a legal contract PDF uploaded by the user.
# This is the MAIN model - everything else links to this.
# ============================================================

class Document(models.Model):
    
    # Status choices for the document processing pipeline
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),       # PDF just uploaded, not processed yet
        ('processing', 'Processing'),   # Currently being analyzed by NLP
        ('completed', 'Completed'),     # NLP processing done successfully
        ('failed', 'Failed'),           # Something went wrong during processing
    ]

    # ── Basic Information ──────────────────────────────────
    
    # Original filename of the uploaded PDF (e.g. "contract_acme.pdf")
    file_name = models.CharField(
        max_length=255,
        help_text="Original name of the uploaded PDF file"
    )

    # The actual PDF file stored in media/contracts/ folder
    file = models.FileField(
        upload_to='contracts/',
        help_text="Uploaded PDF file"
    )

    # Size of the file in bytes (we calculate this when saving)
    file_size = models.PositiveIntegerField(
        default=0,
        help_text="File size in bytes"
    )

    # ── Contract Metadata ──────────────────────────────────

    # Name of the company/person who sent this contract
    counterparty_name = models.CharField(
        max_length=255,
        blank=True,        # Optional field
        null=True,
        help_text="Name of the other party in the contract"
    )

    # Type of contract: NDA, MSA, Employment, etc.
    contract_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Type of contract e.g. NDA, MSA, Employment"
    )

    # Which country/state law governs this contract
    governing_law = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Governing law jurisdiction e.g. California, India"
    )

    # When does the contract start
    contract_start_date = models.DateField(
        blank=True,
        null=True,
        help_text="Contract start date"
    )

    # When does the contract end
    contract_end_date = models.DateField(
        blank=True,
        null=True,
        help_text="Contract end date"
    )

    # ── Processing Status ──────────────────────────────────

    # Current status of NLP processing
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='uploaded',
        help_text="Current processing status of the document"
    )

    # Number of high-risk clauses found (updated after NLP processing)
    risk_score = models.IntegerField(
        default=0,
        help_text="Number of high-risk clauses found in the document"
    )

    # ── Timestamps ─────────────────────────────────────────

    # Automatically set when document is first uploaded
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the document was uploaded"
    )

    # Automatically updated every time document record is saved
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the document record was last updated"
    )

    # ── Meta Configuration ─────────────────────────────────

    class Meta:
        # Show newest documents first in admin and API
        ordering = ['-uploaded_at']
        
        # Human-readable names in Django Admin
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'

    # String representation - shown in Django Admin list
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
            # Get original filename from the uploaded file
            self.file_name = self.file.name.split('/')[-1]
            
            # Calculate file size in bytes
            try:
                self.file_size = self.file.size
            except Exception:
                self.file_size = 0

        # Call the original save method
        super().save(*args, **kwargs)