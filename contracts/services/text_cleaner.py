# contracts/services/text_cleaner.py

# WHY THIS FILE EXISTS:
# Raw text from PDFs is messy. It has:
#   - Multiple spaces between words (like "This  is   a  contract")
#   - Broken lines (a sentence split across two lines because of PDF formatting)
#   - Special characters like \x0c (form feed) or \xa0 (non-breaking space)
#   - Page numbers scattered throughout
#   - Headers and footers repeated on every page
# This file cleans all that up before we send the text to spaCy.

# ── IMPORTS ───────────────────────────────────────────────────────────────────

# re is Python's built-in regular expressions module
# Regular expressions (regex) let us find patterns in text
# Example: find all numbers, find all words starting with capital letters
import re

# logging for recording events
import logging

# ── LOGGING SETUP ─────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)

# ── MAIN CLEANING FUNCTION ────────────────────────────────────────────────────

def clean_contract_text(raw_text):
    """
    Clean and normalize raw text extracted from a PDF contract.
    
    This function runs the text through multiple cleaning steps.
    Each step removes or fixes one specific type of problem.
    
    Arguments:
        raw_text (str): The raw text string from pdf_extractor.py
    
    Returns:
        str: Cleaned text ready for NLP processing
    
    Example:
        raw  = "This   is  a\\n\\ncontract  between  ACME  Corp.\\x0c"
        clean = clean_contract_text(raw)
        # clean = "This is a contract between ACME Corp."
    """
    
    # Guard against empty or None input
    # If we receive nothing, return an empty string
    if not raw_text:
        logger.warning("clean_contract_text received empty input")
        return ""
    
    # Make a copy so we don't modify the original (good practice)
    text = raw_text
    
    # ── STEP 1: REMOVE SPECIAL PDF CHARACTERS ─────────────────────────────────
    
    # \x0c is a "form feed" character — PDF uses it to mark page breaks
    # We replace it with a newline so pages are still separated
    text = text.replace('\x0c', '\n')
    
    # \xa0 is a "non-breaking space" — looks like a space but isn't
    # Replace it with a regular space
    text = text.replace('\xa0', ' ')
    
    # \t is a tab character — replace with a space
    text = text.replace('\t', ' ')
    
    logger.debug("Step 1 complete: removed special characters")
    
    # ── STEP 2: FIX BROKEN HYPHENATED WORDS ───────────────────────────────────
    
    # PDFs often break long words across lines with a hyphen:
    # "indemni-\nfication" should be "indemnification"
    # Regex pattern: hyphen followed by a newline
    # We replace "hyphen + newline" with nothing (join the word)
    text = re.sub(r'-\n', '', text)
    
    logger.debug("Step 2 complete: fixed hyphenated line breaks")
    
    # ── STEP 3: FIX BROKEN SENTENCES ACROSS LINES ────────────────────────────
    
    # PDFs break sentences mid-line. "The party shall\npay the amount" 
    # should be "The party shall pay the amount"
    # But we should NOT join paragraph breaks (two newlines = paragraph break)
    
    # First, protect paragraph breaks by replacing \n\n with a placeholder
    text = text.replace('\n\n', '<<PARAGRAPH>>')
    
    # Now replace single newlines with a space (joining broken sentences)
    text = text.replace('\n', ' ')
    
    # Restore paragraph breaks as double newlines
    text = text.replace('<<PARAGRAPH>>', '\n\n')
    
    logger.debug("Step 3 complete: fixed broken sentences")
    
    # ── STEP 4: REMOVE PAGE NUMBERS ───────────────────────────────────────────
    
    # Many contracts have "Page 1 of 10", "- 2 -", "Page: 3" etc.
    # re.sub(pattern, replacement, string) replaces all matches of pattern
    # r'' means raw string (backslashes are literal, not escape sequences)
    
    # Pattern: "Page" followed by optional space, then numbers, optional " of N"
    text = re.sub(r'\bPage\s+\d+\s*(of\s*\d+)?\b', '', text, flags=re.IGNORECASE)
    
    # Pattern: standalone numbers at start of line (standalone page numbers)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    
    logger.debug("Step 4 complete: removed page numbers")
    
    # ── STEP 5: REMOVE EXTRA WHITESPACE ──────────────────────────────────────
    
    # Multiple spaces → single space
    # \s+ matches one or more whitespace characters (space, tab, etc.)
    text = re.sub(r'[ \t]+', ' ', text)
    
    # More than 2 consecutive newlines → exactly 2 newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    logger.debug("Step 5 complete: normalized whitespace")
    
    # ── STEP 6: REMOVE COMMON BOILERPLATE HEADERS/FOOTERS ────────────────────
    
    # Many contracts repeat headers like "CONFIDENTIAL" on every page
    # We remove lines that are just short uppercase words (likely headers)
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        stripped_line = line.strip()
        
        # Skip lines that are all uppercase AND short (likely headers/footers)
        # Example: "CONFIDENTIAL", "DRAFT", "INITIALS: ___"
        if stripped_line.isupper() and len(stripped_line) < 30:
            logger.debug(f"Removed likely header/footer: '{stripped_line}'")
            continue
        
        cleaned_lines.append(line)
    
    text = '\n'.join(cleaned_lines)
    
    # ── STEP 7: FINAL STRIP ───────────────────────────────────────────────────
    
    # Remove any leading or trailing whitespace from the entire text
    text = text.strip()
    
    logger.info(f"Text cleaning complete. Final length: {len(text)} characters")
    
    return text


def split_into_clauses(clean_text):
    """
    Split a cleaned contract text into individual clauses/sections.
    
    Legal contracts have numbered clauses like:
    "1. DEFINITIONS", "2. PAYMENT TERMS", "3. INDEMNIFICATION"
    
    This function finds those section headers and splits the text there.
    
    Arguments:
        clean_text (str): The cleaned text from clean_contract_text()
    
    Returns:
        list of dict: Each dict has 'heading' and 'content' keys
        Example: [
            {"heading": "1. DEFINITIONS", "content": "In this agreement..."},
            {"heading": "2. PAYMENT TERMS", "content": "The client shall pay..."}
        ]
    """
    
    if not clean_text:
        return []
    
    # This regex matches typical legal clause headings like:
    # "1." or "1.1" or "ARTICLE 1" or "SECTION 1"
    # ^               = start of a line
    # (\d+\.[\d.]*    = one or more numbers with dots (e.g. 1. or 1.1 or 1.1.2)
    # |ARTICLE\s+\d+  = or "ARTICLE" followed by a number
    # |SECTION\s+\d+) = or "SECTION" followed by a number
    clause_pattern = re.compile(
        r'^(\d+\.[\d.]*|ARTICLE\s+\d+|SECTION\s+\d+)',
        re.MULTILINE | re.IGNORECASE
    )
    
    # finditer() returns all matches with their position in the string
    # We use positions to slice out the text between headings
    matches = list(clause_pattern.finditer(clean_text))
    
    if not matches:
        # No clear clause headings found — treat the whole text as one clause
        logger.warning("No clause headings found — treating text as single block")
        return [{"heading": "FULL CONTRACT", "content": clean_text}]
    
    clauses = []
    
    for i, match in enumerate(matches):
        # heading_start: where this heading begins in the text
        heading_start = match.start()
        
        # heading_end: where this heading ends (and the content begins)
        heading_end = match.end()
        
        # content_end: where this clause's content ends
        # Either at the start of the NEXT heading, or end of text
        if i + 1 < len(matches):
            content_end = matches[i + 1].start()
        else:
            content_end = len(clean_text)
        
        # Extract the heading text and the content text
        heading = clean_text[heading_start:heading_end].strip()
        content = clean_text[heading_end:content_end].strip()
        
        # Only include clauses that actually have content
        if content:
            clauses.append({
                "heading": heading,
                "content": content
            })
    
    logger.info(f"Split text into {len(clauses)} clauses")
    return clauses