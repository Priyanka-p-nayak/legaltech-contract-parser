# contracts/services/contract_processor.py

# WHY THIS FILE EXISTS:
# Member 1 should not have to call 5 different functions from 4 different files.
# This file provides ONE clean function: process_contract()
# Member 1 calls it with a file path, and gets back a complete result dict.
#
# The pipeline order is:
# 1. Extract text from PDF        (pdf_extractor.py)
# 2. Clean the text               (text_cleaner.py)
# 3. Split into clauses           (text_cleaner.py)
# 4. Extract entities             (entity_extractor.py)
# 5. Categorize clauses           (clause_categorizer.py)
# 6. Detect risks                 (risk_detector.py)
# 7. Return complete report

# ── IMPORTS ───────────────────────────────────────────────────────────────────

# Import from our own service files
from .pdf_extractor     import extract_text_from_pdf, get_pdf_metadata
from .text_cleaner      import clean_contract_text, split_into_clauses
from .entity_extractor  import extract_all_entities
from .clause_categorizer import categorize_all_clauses, get_category_summary
from .risk_detector     import scan_contract_for_risks

import logging

# ── LOGGING SETUP ─────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)


# ── MASTER PIPELINE FUNCTION ──────────────────────────────────────────────────

def process_contract(pdf_path):
    """
    Master function: runs the complete NLP pipeline on a contract PDF.

    This is the ONLY function Member 1 needs to call.
    It receives the file path and returns everything.

    Arguments:
        pdf_path (str): Path to the uploaded PDF file
                        Example: "media/contracts/contract_001.pdf"

    Returns:
        dict: Complete analysis results ready to save to the database
        {
            "success": True,
            "extracted_text": "Full contract text...",
            "metadata": {"pages": 5, "author": "..."},
            "entities": {
                "company_names": [...],
                "dates": [...],
                "jurisdiction": "India",
                "contract_duration": "2 years"
            },
            "clauses": [...],
            "category_summary": {...},
            "risk_report": {
                "overall_risk_level": "HIGH",
                "total_risks_found": 5,
                ...
            },
            "error": None
        }
    """

    logger.info(f"=== Starting contract processing: {pdf_path} ===")

    # ── STEP 1: EXTRACT TEXT FROM PDF ─────────────────────────────────────────

    logger.info("Step 1: Extracting text from PDF...")
    raw_text = extract_text_from_pdf(pdf_path)

    # If extraction failed, return early with error info
    if not raw_text:
        logger.error(f"Text extraction failed for: {pdf_path}")
        return {
            "success":        False,
            "error":          "Could not extract text from PDF. The file may be corrupted, password-protected, or image-only.",
            "extracted_text": "",
            "metadata":       {},
            "entities":       {},
            "clauses":        [],
            "category_summary": {},
            "risk_report":    {},
        }

    # Get PDF metadata (page count, author, etc.)
    metadata = get_pdf_metadata(pdf_path)
    logger.info(f"Step 1 complete: {len(raw_text)} characters extracted")

    # ── STEP 2: CLEAN THE TEXT ────────────────────────────────────────────────

    logger.info("Step 2: Cleaning text...")
    clean_text = clean_contract_text(raw_text)
    logger.info(f"Step 2 complete: {len(clean_text)} characters after cleaning")

    # ── STEP 3: SPLIT INTO CLAUSES ────────────────────────────────────────────

    logger.info("Step 3: Splitting into clauses...")
    clauses = split_into_clauses(clean_text)
    logger.info(f"Step 3 complete: {len(clauses)} clauses found")

    # ── STEP 4: EXTRACT ENTITIES ──────────────────────────────────────────────

    logger.info("Step 4: Extracting entities...")
    entities = extract_all_entities(clean_text)
    logger.info(f"Step 4 complete: {entities}")

    # ── STEP 5: CATEGORIZE CLAUSES ────────────────────────────────────────────

    logger.info("Step 5: Categorizing clauses...")
    categorized_clauses  = categorize_all_clauses(clauses)
    category_summary     = get_category_summary(categorized_clauses)
    logger.info(f"Step 5 complete: categories found: {list(category_summary.keys())}")

    # ── STEP 6: DETECT RISKS ──────────────────────────────────────────────────

    logger.info("Step 6: Running risk detection...")
    risk_report = scan_contract_for_risks(categorized_clauses)
    logger.info(
        f"Step 6 complete: Overall risk = {risk_report['overall_risk_level']}"
    )

    # ── STEP 7: BUILD FINAL RESULT ────────────────────────────────────────────

    result = {
        "success":          True,
        "error":            None,
        "extracted_text":   clean_text,
        "metadata":         metadata,
        "entities":         entities,
        "clauses":          categorized_clauses,
        "category_summary": category_summary,
        "risk_report":      risk_report,
    }

    logger.info(f"=== Contract processing complete for: {pdf_path} ===")
    return result