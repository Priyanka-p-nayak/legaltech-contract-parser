# contracts/services/entity_extractor.py

# WHY THIS FILE EXISTS:
# After cleaning the PDF text, we need to find important information:
#   1. Company names (who are the parties to this contract?)
#   2. Dates (when does it start and end?)
#   3. Contract duration (how long is this contract?)
#   4. Jurisdiction (which country's/state's law governs this?)
# This file uses spaCy's NER + custom patterns to find all of these.

# ── IMPORTS ───────────────────────────────────────────────────────────────────

# spacy for NLP processing
import spacy

# Matcher lets us write custom word patterns
from spacy.matcher import Matcher

# re for regex patterns (used for duration extraction)
import re

# logging for recording events
import logging

# ── LOGGING SETUP ─────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)

# ── LOAD SPACY MODEL ──────────────────────────────────────────────────────────

# We load the model once at module level (not inside each function)
# Why? Loading a spaCy model takes ~1 second.
# If we loaded it inside a function, every contract would wait 1 second.
# Loading once at startup means every function call is instant.
try:
    nlp = spacy.load("en_core_web_sm")
    logger.info("spaCy model loaded successfully")
except OSError:
    # This error means the model wasn't downloaded
    logger.error("spaCy model not found. Run: python -m spacy download en_core_web_sm")
    raise


# ── FUNCTION 1: EXTRACT COMPANY NAMES ────────────────────────────────────────

def extract_company_names(clean_text):
    """
    Find all company/organization names mentioned in the contract.

    Uses spaCy's built-in NER to find ORG entities.
    Also applies custom cleanup to remove false positives.

    Arguments:
        clean_text (str): Cleaned contract text from text_cleaner.py

    Returns:
        list: Unique company names found
        Example: ["Tata Consultancy Services Limited", "Reliance Industries Ltd"]
    """

    if not clean_text:
        logger.warning("extract_company_names received empty text")
        return []

    # Process the text through spaCy
    # For long contracts, we limit to first 100,000 characters
    # spaCy has a default limit — we respect it here
    doc = nlp(clean_text[:100000])

    # Collect all ORG entities
    companies = []

    for entity in doc.ents:

        # entity.label_ == "ORG" means spaCy identified it as an organization
        if entity.label_ == "ORG":

            # Get the text and clean it up
            company_name = entity.text.strip()

            # ── FILTERS: Remove false positives ───────────────────────────────

            # Skip if the name is too short (less than 3 characters)
            # "AB" is probably not a company name
            if len(company_name) < 3:
                continue

            # Skip if the name is just a number
            if company_name.isdigit():
                continue

            # Skip common legal words that spaCy mistakes for companies
            # These words often appear in contracts but are not company names
            false_positives = {
                "agreement", "contract", "party", "parties",
                "schedule", "annex", "exhibit", "appendix",
                "clause", "section", "article", "hereinafter",
                "whereas", "therefore", "witness"
            }

            if company_name.lower() in false_positives:
                continue

            # Add to list if not already there (avoid duplicates)
            if company_name not in companies:
                companies.append(company_name)

    logger.info(f"Found {len(companies)} company names")
    return companies


# ── FUNCTION 2: EXTRACT DATES ─────────────────────────────────────────────────

def extract_dates(clean_text):
    """
    Find all dates mentioned in the contract.

    Uses spaCy's DATE entity detection.
    Contracts usually have:
    - Effective date (when it starts)
    - Expiry date (when it ends)
    - Signing date

    Arguments:
        clean_text (str): Cleaned contract text

    Returns:
        list: All date strings found
        Example: ["January 1, 2024", "December 31, 2025", "30 days"]
    """

    if not clean_text:
        return []

    doc = nlp(clean_text[:100000])

    dates = []

    for entity in doc.ents:

        # DATE label includes both specific dates and relative dates
        # Example specific: "January 15, 2024"
        # Example relative: "30 days", "three months"
        if entity.label_ == "DATE":

            date_text = entity.text.strip()

            # Filter out very short date strings (likely noise)
            if len(date_text) < 4:
                continue

            # Avoid duplicates
            if date_text not in dates:
                dates.append(date_text)

    logger.info(f"Found {len(dates)} dates")
    return dates


# ── FUNCTION 3: EXTRACT JURISDICTION ──────────────────────────────────────────

def extract_jurisdiction(clean_text):
    """
    Find which country or state's law governs this contract.

    Jurisdiction phrases look like:
    - "governed by the laws of India"
    - "subject to the laws of England and Wales"
    - "under the laws of California"
    - "governing law: New York"

    We use both regex patterns AND spaCy Matcher to find these.

    Arguments:
        clean_text (str): Cleaned contract text

    Returns:
        str: The jurisdiction found, or "Not specified" if not found
        Example: "India" or "England and Wales" or "New York"
    """

    if not clean_text:
        return "Not specified"

    # ── METHOD 1: REGEX PATTERNS ───────────────────────────────────────────────

    # These regex patterns match common jurisdiction phrases in contracts
    # re.IGNORECASE means it matches regardless of uppercase/lowercase

    jurisdiction_patterns = [
        # "governed by the laws of India"
        r'governed\s+by\s+the\s+laws\s+of\s+([A-Z][a-zA-Z\s]+?)(?:\.|,|and)',

        # "subject to the laws of England"
        r'subject\s+to\s+the\s+laws\s+of\s+([A-Z][a-zA-Z\s]+?)(?:\.|,|and)',

        # "under the laws of California"
        r'under\s+the\s+laws\s+of\s+([A-Z][a-zA-Z\s]+?)(?:\.|,|and)',

        # "laws of the State of New York"
        r'laws\s+of\s+the\s+[Ss]tate\s+of\s+([A-Z][a-zA-Z\s]+?)(?:\.|,|and)',

        # "Governing Law: India"
        r'[Gg]overning\s+[Ll]aw\s*[:\-]\s*([A-Z][a-zA-Z\s]+?)(?:\.|,|\n)',

        # "jurisdiction of the courts of Mumbai"
        r'jurisdiction\s+of\s+the\s+courts\s+of\s+([A-Z][a-zA-Z\s]+?)(?:\.|,|and)',
    ]

    for pattern in jurisdiction_patterns:
        # re.search() finds the FIRST match of the pattern in the text
        match = re.search(pattern, clean_text, re.IGNORECASE)

        if match:
            # group(1) returns the first capture group — the country/state name
            jurisdiction = match.group(1).strip()

            # Clean up trailing words that got captured
            # Remove words like "and", "the", "any" from the end
            jurisdiction = re.sub(
                r'\s+(and|the|any|all|its|this|that)$',
                '',
                jurisdiction,
                flags=re.IGNORECASE
            ).strip()

            logger.info(f"Jurisdiction found via regex: {jurisdiction}")
            return jurisdiction

    # ── METHOD 2: SPACY GPE ENTITIES NEAR KEYWORDS ────────────────────────────

    # If regex didn't find anything, look for GPE entities
    # near jurisdiction keywords using spaCy

    doc = nlp(clean_text[:100000])

    # Keywords that suggest jurisdiction discussion
    jurisdiction_keywords = {
        "governed", "jurisdiction", "governing", "applicable law",
        "choice of law", "courts of"
    }

    # Look through sentences for jurisdiction keywords
    for sent in doc.sents:
        sent_lower = sent.text.lower()

        # Check if this sentence contains any jurisdiction keyword
        if any(keyword in sent_lower for keyword in jurisdiction_keywords):

            # Find GPE (country/city) entities in this sentence
            for ent in sent.ents:
                if ent.label_ == "GPE":
                    jurisdiction = ent.text.strip()
                    logger.info(f"Jurisdiction found via spaCy GPE: {jurisdiction}")
                    return jurisdiction

    # If nothing found
    logger.warning("No jurisdiction found in contract")
    return "Not specified"


# ── FUNCTION 4: EXTRACT CONTRACT DURATION ────────────────────────────────────

def extract_contract_duration(clean_text):
    """
    Find how long the contract lasts.

    Duration phrases look like:
    - "for a period of two (2) years"
    - "for a term of 12 months"
    - "for 3 years from the effective date"
    - "valid for one year"

    Arguments:
        clean_text (str): Cleaned contract text

    Returns:
        str: The duration found, or "Not specified"
        Example: "2 years" or "12 months"
    """

    if not clean_text:
        return "Not specified"

    # Regex patterns for duration
    duration_patterns = [
        # "for a period of two (2) years"
        r'for\s+a\s+period\s+of\s+([\w\s\(\)]+?(?:year|month|day)s?)',

        # "for a term of 12 months"
        r'for\s+a\s+term\s+of\s+([\w\s]+?(?:year|month|day)s?)',

        # "for 3 years"
        r'for\s+(\d+\s+(?:year|month|day)s?)',

        # "valid for one year"
        r'valid\s+for\s+([\w\s]+?(?:year|month|day)s?)',

        # "term of this agreement is 2 years"
        r'term\s+of\s+this\s+[Aa]greement\s+(?:is|shall be)\s+([\w\s]+?(?:year|month|day)s?)',
    ]

    for pattern in duration_patterns:
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match:
            duration = match.group(1).strip()
            # Clean up extra spaces
            duration = re.sub(r'\s+', ' ', duration)
            logger.info(f"Contract duration found: {duration}")
            return duration

    logger.warning("No contract duration found")
    return "Not specified"


# ── FUNCTION 5: EXTRACT ALL ENTITIES (MASTER FUNCTION) ────────────────────────

def extract_all_entities(clean_text):
    """
    Master function that runs ALL extraction functions and returns
    everything in one organized dictionary.

    This is the function that Member 1 will call from views.py.
    It receives clean text and returns a complete dictionary of findings.

    Arguments:
        clean_text (str): Cleaned contract text from text_cleaner.py

    Returns:
        dict: All extracted entities
        Example:
        {
            "company_names": ["Tata Consultancy Services", "Reliance Ltd"],
            "dates": ["January 1, 2024", "December 31, 2025"],
            "jurisdiction": "India",
            "contract_duration": "2 years",
            "extraction_successful": True
        }
    """

    logger.info("Starting full entity extraction...")

    # Run all four extraction functions
    company_names    = extract_company_names(clean_text)
    dates            = extract_dates(clean_text)
    jurisdiction     = extract_jurisdiction(clean_text)
    contract_duration = extract_contract_duration(clean_text)

    # Build result dictionary
    result = {
        "company_names":      company_names,
        "dates":              dates,
        "jurisdiction":       jurisdiction,
        "contract_duration":  contract_duration,
        "extraction_successful": True
    }

    logger.info(f"Entity extraction complete: {result}")
    return result