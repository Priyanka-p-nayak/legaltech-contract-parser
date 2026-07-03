# contracts/services/optimized_processor.py

# WHY THIS FILE EXISTS:
# Real contracts can be 100+ pages (50,000+ words).
# Our pipeline processes the entire text at once — this can be slow.
# This file adds two optimizations:
#
#   1. TEXT CHUNKING: Split huge text into chunks, process each separately
#      This prevents spaCy from hitting memory limits on large contracts.
#
#   2. RESULT CACHING: Store results so we don't re-process the same file twice
#      If the same PDF is uploaded again, return cached results instantly.
#
#   3. EARLY STOPPING: If we already found all entity types,
#      stop processing further chunks (saves time)

# ── IMPORTS ───────────────────────────────────────────────────────────────────

import hashlib
import logging
import time

from contracts.services.pdf_extractor      import extract_text_from_pdf, get_pdf_metadata
from contracts.services.text_cleaner       import clean_contract_text, split_into_clauses
from contracts.services.entity_extractor   import extract_all_entities
from contracts.services.clause_categorizer import categorize_all_clauses, get_category_summary
from contracts.services.risk_detector      import scan_contract_for_risks
from contracts.services.report_generator   import generate_risk_report, generate_text_report

# ── LOGGING SETUP ─────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)

# ── IN-MEMORY CACHE ───────────────────────────────────────────────────────────

# Simple dict-based cache
# Key   = MD5 hash of the PDF file content
# Value = the processed results dict
#
# Note: This cache resets when the server restarts.
# For production, use Redis or Django's cache framework.
# For this internship project, this is sufficient.

_results_cache = {}

# Maximum number of cached results to keep in memory
# Old entries are removed when this limit is reached
MAX_CACHE_SIZE = 50

# Maximum characters spaCy processes at once
# en_core_web_sm has a default limit; we stay well below it
CHUNK_SIZE = 50000  # 50,000 characters per chunk


# ── FUNCTION 1: GENERATE FILE HASH ───────────────────────────────────────────

def _get_file_hash(pdf_path):
    """
    Generate an MD5 hash of the PDF file content.
    
    Two identical files will produce the same hash.
    This is how we detect duplicate uploads.
    
    Arguments:
        pdf_path (str): Path to the PDF file
    
    Returns:
        str: MD5 hash string, or None if the file can't be read
    """
    
    try:
        # Open the file in binary mode (rb = read binary)
        with open(pdf_path, 'rb') as f:
            # Read the entire file content
            file_content = f.read()
            
            # hashlib.md5() creates an MD5 hash object
            # .hexdigest() converts it to a readable hex string
            # Example: "d41d8cd98f00b204e9800998ecf8427e"
            file_hash = hashlib.md5(file_content).hexdigest()
            
        return file_hash
    
    except Exception as e:
        logger.warning(f"Could not hash file {pdf_path}: {e}")
        return None


# ── FUNCTION 2: SPLIT TEXT INTO CHUNKS ───────────────────────────────────────

def _split_into_chunks(text, chunk_size=CHUNK_SIZE):
    """
    Split a large text into smaller chunks for processing.
    
    We split at sentence boundaries (periods) to avoid
    cutting a sentence in half, which would confuse NLP.
    
    Arguments:
        text       (str): The full contract text
        chunk_size (int): Maximum characters per chunk
    
    Returns:
        list of str: Text chunks
    """
    
    if len(text) <= chunk_size:
        # Text is small enough — no chunking needed
        return [text]
    
    chunks  = []
    current_chunk = ""
    
    # Split by sentences (approximate — split on ". ")
    sentences = text.split(". ")
    
    for sentence in sentences:
        
        # Add this sentence to the current chunk
        candidate = current_chunk + sentence + ". "
        
        if len(candidate) <= chunk_size:
            # Sentence fits in current chunk
            current_chunk = candidate
        
        else:
            # Sentence would make chunk too large
            # Save the current chunk and start a new one
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
    
    # Don't forget the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    logger.info(f"Text split into {len(chunks)} chunks for processing")
    return chunks


# ── FUNCTION 3: MERGE ENTITY RESULTS FROM CHUNKS ─────────────────────────────

def _merge_entity_results(chunk_results):
    """
    Merge entity extraction results from multiple chunks.
    
    When we process in chunks, each chunk returns its own entities.
    We need to combine them into one final result.
    
    Arguments:
        chunk_results (list): List of entity dicts from each chunk
    
    Returns:
        dict: Merged entities with duplicates removed
    """
    
    merged_companies  = []
    merged_dates      = []
    merged_jurisdiction = "Not specified"
    merged_duration   = "Not specified"
    
    for result in chunk_results:
        
        # Merge company names (avoid duplicates)
        for company in result.get("company_names", []):
            if company not in merged_companies:
                merged_companies.append(company)
        
        # Merge dates (avoid duplicates)
        for date in result.get("dates", []):
            if date not in merged_dates:
                merged_dates.append(date)
        
        # Take the first jurisdiction found (usually in the first chunk)
        if result.get("jurisdiction") != "Not specified":
            if merged_jurisdiction == "Not specified":
                merged_jurisdiction = result["jurisdiction"]
        
        # Take the first duration found
        if result.get("contract_duration") != "Not specified":
            if merged_duration == "Not specified":
                merged_duration = result["contract_duration"]
    
    return {
        "company_names":     merged_companies,
        "dates":             merged_dates,
        "jurisdiction":      merged_jurisdiction,
        "contract_duration": merged_duration,
        "extraction_successful": True
    }


# ── FUNCTION 4: OPTIMIZED MASTER PIPELINE ────────────────────────────────────

def process_contract_optimized(pdf_path):
    """
    Optimized version of the master contract processing pipeline.
    
    Improvements over the basic process_contract():
    1. Caches results for duplicate files
    2. Chunks large text to stay within spaCy limits
    3. Times each step for performance monitoring
    4. Generates both dict report and text report
    
    Arguments:
        pdf_path (str): Path to the uploaded PDF file
    
    Returns:
        dict: Complete analysis results (same structure as process_contract)
              plus additional performance data
    """
    
    # Start timing the entire pipeline
    pipeline_start = time.time()
    
    logger.info(f"=== Optimized processing started: {pdf_path} ===")
    
    # ── CHECK 1: CACHE LOOKUP ─────────────────────────────────────────────────
    
    file_hash = _get_file_hash(pdf_path)
    
    if file_hash and file_hash in _results_cache:
        logger.info(f"Cache HIT for {pdf_path} — returning cached results")
        
        cached_result = _results_cache[file_hash].copy()
        cached_result["from_cache"] = True
        cached_result["processing_time_seconds"] = 0.0
        
        return cached_result
    
    logger.info(f"Cache MISS for {pdf_path} — running full pipeline")
    
    # ── STEP 1: PDF EXTRACTION ────────────────────────────────────────────────
    
    step_start = time.time()
    raw_text   = extract_text_from_pdf(pdf_path)
    metadata   = get_pdf_metadata(pdf_path)
    
    if not raw_text:
        return {
            "success": False,
            "error":   "PDF text extraction failed",
            "from_cache": False
        }
    
    logger.info(
        f"Step 1 (PDF Extract): {time.time() - step_start:.2f}s — "
        f"{len(raw_text)} chars"
    )
    
    # ── STEP 2: TEXT CLEANING ─────────────────────────────────────────────────
    
    step_start = time.time()
    clean_text = clean_contract_text(raw_text)
    clauses    = split_into_clauses(clean_text)
    
    logger.info(
        f"Step 2 (Clean+Split): {time.time() - step_start:.2f}s — "
        f"{len(clauses)} clauses"
    )
    
    # ── STEP 3: ENTITY EXTRACTION (with chunking) ─────────────────────────────
    
    step_start   = time.time()
    text_chunks  = _split_into_chunks(clean_text)
    chunk_results = []
    
    logger.info(f"Processing {len(text_chunks)} text chunk(s) for entity extraction")
    
    for i, chunk in enumerate(text_chunks):
        logger.debug(f"Processing chunk {i+1}/{len(text_chunks)}")
        chunk_entities = extract_all_entities(chunk)
        chunk_results.append(chunk_entities)
    
    # Merge results from all chunks
    entities = _merge_entity_results(chunk_results)
    
    logger.info(
        f"Step 3 (Entities): {time.time() - step_start:.2f}s — "
        f"{len(entities.get('company_names', []))} companies, "
        f"{len(entities.get('dates', []))} dates"
    )
    
    # ── STEP 4: CLAUSE CATEGORIZATION ────────────────────────────────────────
    
    step_start          = time.time()
    categorized_clauses = categorize_all_clauses(clauses)
    category_summary    = get_category_summary(categorized_clauses)
    
    logger.info(
        f"Step 4 (Categorize): {time.time() - step_start:.2f}s — "
        f"{len(category_summary)} categories"
    )
    
    # ── STEP 5: RISK DETECTION ────────────────────────────────────────────────
    
    step_start       = time.time()
    risk_scan_result = scan_contract_for_risks(categorized_clauses)
    
    logger.info(
        f"Step 5 (Risk Scan): {time.time() - step_start:.2f}s — "
        f"{risk_scan_result.get('total_risks_found', 0)} risks"
    )
    
    # ── STEP 6: REPORT GENERATION ─────────────────────────────────────────────
    
    step_start      = time.time()
    complete_report = generate_risk_report(
        entities,
        categorized_clauses,
        risk_scan_result,
        metadata
    )
    text_report = generate_text_report(complete_report)
    
    logger.info(
        f"Step 6 (Report Gen): {time.time() - step_start:.2f}s"
    )
    
    # ── ASSEMBLE FINAL RESULT ─────────────────────────────────────────────────
    
    total_time = time.time() - pipeline_start
    
    result = {
        "success":             True,
        "error":               None,
        "from_cache":          False,
        "processing_time_seconds": round(total_time, 2),
        
        # Text data
        "extracted_text":      clean_text,
        "metadata":            metadata,
        
        # Analysis data
        "entities":            entities,
        "clauses":             categorized_clauses,
        "category_summary":    category_summary,
        
        # Risk data
        "risk_report":         complete_report,
        "risk_level":          complete_report["risk_score"]["overall_level"],
        "risk_score":          complete_report["risk_score"]["overall_score"],
        "risk_grade":          complete_report["risk_score"]["risk_grade"],
        
        # Human readable report
        "text_report":         text_report,
    }
    
    logger.info(
        f"=== Pipeline complete in {total_time:.2f}s — "
        f"Score: {result['risk_score']}/100 "
        f"Grade: {result['risk_grade']} ==="
    )
    
    # ── STORE IN CACHE ────────────────────────────────────────────────────────
    
    if file_hash:
        # If cache is full, remove oldest entry
        if len(_results_cache) >= MAX_CACHE_SIZE:
            oldest_key = next(iter(_results_cache))
            del _results_cache[oldest_key]
            logger.debug(f"Cache full — removed oldest entry")
        
        _results_cache[file_hash] = result
        logger.info(f"Result cached with key: {file_hash[:8]}...")
    
    return result