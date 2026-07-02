# contracts/signals.py

# WHY THIS FILE EXISTS:
# Django signals let one part of the code react to events in another part.
# The 'post_save' signal fires every time a model instance is saved.
# We listen for Contract saves and automatically run our NLP pipeline.
#
# This means Member 1 does NOT need to call our code manually.
# The signal handles it automatically — clean separation of work.

# ── IMPORTS ───────────────────────────────────────────────────────────────────

# post_save signal fires after any model's .save() method completes
from django.db.models.signals import post_save

# receiver decorator registers a function as a signal handler
from django.dispatch import receiver

# We import the Contract model to listen for its save events
# Note: we import inside the function to avoid circular imports
# (explained below)

# Our master pipeline function
from contracts.services.contract_processor import process_contract

import logging

# ── LOGGING SETUP ─────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)


# ── SIGNAL HANDLER ────────────────────────────────────────────────────────────

# The @receiver decorator connects this function to the post_save signal
# sender=Contract means this only fires when a Contract is saved
# (not when other models like User or Admin are saved)
@receiver(post_save, sender='contracts.Contract')
def process_contract_after_save(sender, instance, created, **kwargs):
    """
    Automatically process a contract after it is saved to the database.
    
    This function is called automatically by Django whenever a Contract
    object is saved. We check if it's a NEW contract (created=True)
    and if it hasn't been processed yet.
    
    Arguments:
        sender   : The model class (Contract)
        instance : The actual Contract object that was saved
        created  : True if this is a NEW record, False if it's an UPDATE
        **kwargs : Extra arguments Django passes (we don't use these)
    
    Returns:
        None (results are saved directly to the database)
    """
    
    # ── STEP 1: ONLY PROCESS NEW CONTRACTS ────────────────────────────────────
    
    # 'created' is True only when a NEW contract is saved for the first time
    # We don't want to re-process every time the contract is updated
    # (e.g., when we save the results back, it would create an infinite loop!)
    if not created:
        logger.debug(f"Contract {instance.id} updated — skipping re-processing")
        return
    
    # ── STEP 2: CHECK IF FILE EXISTS ──────────────────────────────────────────
    
    # Make sure the contract has a file attached
    if not instance.file:
        logger.warning(f"Contract {instance.id} has no file — cannot process")
        return
    
    # ── STEP 3: CHECK IF ALREADY PROCESSED ───────────────────────────────────
    
    # If extracted_text already has content, it was processed before
    # This prevents re-processing if someone calls this signal manually
    if instance.extracted_text:
        logger.info(f"Contract {instance.id} already processed — skipping")
        return
    
    # ── STEP 4: GET THE FILE PATH ──────────────────────────────────────────────
    
    # instance.file.path gives the full file path on disk
    # Example: "/home/user/project/media/contracts/contract_001.pdf"
    try:
        pdf_path = instance.file.path
        logger.info(f"Starting NLP processing for Contract {instance.id}: {pdf_path}")
    
    except Exception as e:
        logger.error(f"Could not get file path for Contract {instance.id}: {e}")
        return
    
    # ── STEP 5: RUN THE NLP PIPELINE ──────────────────────────────────────────
    
    try:
        # Call our master pipeline function
        # This runs: extract → clean → entities → categorize → risks
        results = process_contract(pdf_path)
    
    except Exception as e:
        logger.error(f"Pipeline failed for Contract {instance.id}: {e}")
        return
    
    # ── STEP 6: CHECK IF PIPELINE SUCCEEDED ──────────────────────────────────
    
    if not results.get("success"):
        # Pipeline failed — save the error message
        logger.error(
            f"Contract {instance.id} processing failed: "
            f"{results.get('error', 'Unknown error')}"
        )
        
        # Save error status to DB so Member 3 can show it on dashboard
        # We use update() instead of save() to avoid triggering the signal again
        from contracts.models import Contract
        Contract.objects.filter(id=instance.id).update(
            processing_status='FAILED',
            processing_error=results.get('error', 'Unknown error')
        )
        return
    
    # ── STEP 7: SAVE RESULTS TO DATABASE ─────────────────────────────────────
    
    # We use .update() on the queryset instead of instance.save()
    # WHY? Because instance.save() would trigger post_save again
    # creating an INFINITE LOOP:
    #   save() → signal → process() → save() → signal → process() → ...
    # .update() writes directly to DB without triggering signals
    
    try:
        from contracts.models import Contract
        
        entities    = results.get("entities", {})
        risk_report = results.get("risk_report", {})
        
        Contract.objects.filter(id=instance.id).update(
            # Raw extracted and cleaned text
            extracted_text = results.get("extracted_text", ""),
            
            # Entity data (stored as JSON in DB)
            company_names  = entities.get("company_names", []),
            dates_found    = entities.get("dates", []),
            jurisdiction   = entities.get("jurisdiction", "Not specified"),
            contract_duration = entities.get("contract_duration", "Not specified"),
            
            # Risk analysis
            risk_level     = risk_report.get("overall_risk_level", "LOW"),
            risk_report    = risk_report,
            
            # Clause data
            clauses        = results.get("clauses", []),
            category_summary = results.get("category_summary", {}),
            
            # Mark as successfully processed
            processing_status = 'COMPLETED',
            processing_error  = None,
        )
        
        logger.info(
            f"Contract {instance.id} processed successfully. "
            f"Risk: {risk_report.get('overall_risk_level')} | "
            f"Companies: {len(entities.get('company_names', []))} | "
            f"Risks found: {risk_report.get('total_risks_found', 0)}"
        )
    
    except Exception as e:
        logger.error(f"Failed to save results for Contract {instance.id}: {e}")