"""
validators.py
=============
Reusable validation functions and constants used across
serializers.py, views.py, and nlp_views.py.

Centralizing these means every "what counts as a valid
severity / status / page number" rule is defined exactly
ONCE — change it here and every endpoint that checks it
stays in sync automatically.
"""

import os
from datetime import datetime

from .exceptions import (
    EmptyFileException,
    EmptyRequestBodyException,
    FileTooLargeException,
    InvalidFileTypeException,
    InvalidSeverityException,
    InvalidStatusException,
    NoFileProvidedException,
)


# ============================================================
# CONSTANTS
# ============================================================

ALLOWED_STATUSES = [
    'uploaded',
    'processing',
    'completed',
    'failed',
]

ALLOWED_SEVERITIES = [
    'low',
    'medium',
    'high',
]

ALLOWED_CLAUSE_TYPES = [
    'confidentiality',
    'termination',
    'indemnification',
    'governing_law',
    'limitation_of_liability',
    'intellectual_property',
    'dispute_resolution',
    'payment_terms',
    'warranties',
    'force_majeure',
    'other',
]

ALLOWED_ORDERINGS = [
    'uploaded_at',
    '-uploaded_at',
    'risk_score',
    '-risk_score',
]

# 10 MB in bytes
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Minimum file size (must not be empty)
MIN_FILE_SIZE_BYTES = 1

# Allowed file extensions
ALLOWED_EXTENSIONS = ['.pdf']

# Text field limits.
# WHY these specific numbers: clause_text gets the largest
# limit (50,000 chars) because a single legal clause can
# legitimately span a full page or more of dense text.
# Shorter fields like risk_title are capped much lower since
# they're meant to be a one-line summary, not a paragraph.
# See test_edge_cases.py for the exact boundary tests proving
# these limits are enforced correctly at both ends.
MAX_CLAUSE_TEXT_LENGTH    = 50000   # 50,000 characters
MAX_RISK_TITLE_LENGTH     = 500     # 500 characters
MAX_FLAGGED_TEXT_LENGTH   = 10000   # 10,000 characters
MAX_EXPLANATION_LENGTH    = 5000    # 5,000 characters
MAX_COUNTERPARTY_LENGTH   = 500     # 500 characters
MAX_GOVERNING_LAW_LENGTH  = 500     # 500 characters
MAX_CONTRACT_TYPE_LENGTH  = 200     # 200 characters

# Page number limits
MAX_PAGE_NUMBER = 10000

# Risk score limit
MAX_RISK_SCORE  = 10000


# ============================================================
# FILE VALIDATORS
# ============================================================

def validate_pdf_file(file):
    """
    Validates uploaded file with specific exceptions
    for each type of error.
    """
    from .exceptions import (
        NoFileProvidedException,
        InvalidFileTypeException,
        EmptyFileException,
        FileTooLargeException,
    )

    # Check 1: File exists
    if file is None:
        raise NoFileProvidedException()

    # Check 2: Extension is .pdf
    file_name = file.name.lower()
    _, ext    = os.path.splitext(file_name)

    if ext not in ALLOWED_EXTENSIONS:
        raise InvalidFileTypeException(
            detail=(
                f"'{file.name}' is not allowed. "
                f"Only PDF files (.pdf) are accepted."
            )
        )

    # Check 3: File is not empty
    if file.size < MIN_FILE_SIZE_BYTES:
        raise EmptyFileException()

    # Check 4: File not too large
    if file.size > MAX_FILE_SIZE_BYTES:
        size_mb = file.size / (1024 * 1024)
        raise FileTooLargeException(
            detail=(
                f"File size {size_mb:.1f}MB exceeds "
                f"the 10MB limit. Please compress your PDF."
            )
        )

    return file


# ============================================================
# STATUS VALIDATORS
# ============================================================

def validate_document_status(status_value):
    """
    Validates status is one of allowed values.
    Also strips whitespace before checking.
    Raises InvalidStatusException if not valid.
    """
    # Strip whitespace
    if isinstance(status_value, str):
        status_value = status_value.strip()

    if status_value not in ALLOWED_STATUSES:
        raise InvalidStatusException(
            detail=(
                f"'{status_value}' is not valid. "
                f"Allowed: {', '.join(ALLOWED_STATUSES)}"
            )
        )
    return status_value


# ============================================================
# SEVERITY VALIDATORS
# ============================================================

def validate_severity(severity_value):
    """
    Validates severity is low, medium, or high.
    Raises InvalidSeverityException if not valid.
    """
    if isinstance(severity_value, str):
        severity_value = severity_value.strip().lower()

    if severity_value not in ALLOWED_SEVERITIES:
        raise InvalidSeverityException(
            detail=(
                f"'{severity_value}' is not valid. "
                f"Allowed: {', '.join(ALLOWED_SEVERITIES)}"
            )
        )
    return severity_value


# ============================================================
# REQUEST BODY VALIDATORS
# ============================================================

def validate_request_body(data):
    """
    Validates request body is not empty or None.
    Also checks that it is not just an empty dict.
    Raises EmptyRequestBodyException if empty.
    """
    if data is None or data == {} or data == []:
        raise EmptyRequestBodyException()
    return data


# ============================================================
# NUMERIC VALIDATORS
# ============================================================

def validate_confidence_score(score):
    """
    Validates confidence score:
    - Must be a number
    - Must be between 0.0 and 1.0 inclusive
    """
    try:
        score = float(score)
    except (TypeError, ValueError):
        raise ValueError(
            "Confidence score must be a number between 0.0 and 1.0"
        )

    if score < 0.0 or score > 1.0:
        raise ValueError(
            f"Confidence score {score} is invalid. "
            f"Must be between 0.0 and 1.0"
        )
    return round(score, 6)


def validate_page_number(page_num):
    """
    Validates page number:
    - Must be an integer
    - Must be >= 1
    - Must be <= MAX_PAGE_NUMBER (10000)
    """
    try:
        page_num = int(page_num)
    except (TypeError, ValueError):
        raise ValueError(
            "Page number must be a positive integer"
        )

    if page_num < 1:
        raise ValueError(
            f"Page number {page_num} is invalid. "
            f"Must be 1 or greater."
        )

    if page_num > MAX_PAGE_NUMBER:
        raise ValueError(
            f"Page number {page_num} is too large. "
            f"Maximum allowed is {MAX_PAGE_NUMBER}."
        )
    return page_num


def validate_risk_score(score):
    """
    Validates risk score:
    - Must be an integer
    - Must be >= 0
    - Must be <= MAX_RISK_SCORE
    """
    try:
        score = int(score)
    except (TypeError, ValueError):
        raise ValueError(
            "Risk score must be a non-negative integer"
        )

    if score < 0:
        raise ValueError(
            f"Risk score {score} is invalid. "
            f"Must be 0 or greater."
        )

    if score > MAX_RISK_SCORE:
        raise ValueError(
            f"Risk score {score} is too large. "
            f"Maximum allowed is {MAX_RISK_SCORE}."
        )
    return score


# ============================================================
# TEXT VALIDATORS
# ============================================================

def validate_text_not_empty(text, field_name='Text'):
    """
    Validates text field:
    - Must not be None
    - Must not be empty after stripping whitespace
    - Must not be only whitespace
    """
    if text is None:
        raise ValueError(f"{field_name} cannot be None.")

    if not isinstance(text, str):
        raise ValueError(f"{field_name} must be a string.")

    if not text.strip():
        raise ValueError(
            f"{field_name} cannot be empty or only whitespace."
        )
    return text.strip()


def validate_clause_text(text):
    """
    Validates clause text:
    - Must not be empty
    - Minimum 10 characters after stripping
    - Maximum 50,000 characters
    """
    text = validate_text_not_empty(text, 'Clause text')

    if len(text) < 10:
        raise ValueError(
            "Clause text is too short. "
            "Minimum 10 characters required."
        )

    if len(text) > MAX_CLAUSE_TEXT_LENGTH:
        raise ValueError(
            f"Clause text is too long. "
            f"Maximum {MAX_CLAUSE_TEXT_LENGTH} characters allowed."
        )
    return text


def validate_risk_title(title):
    """
    Validates risk title:
    - Must not be empty
    - Maximum 500 characters
    """
    title = validate_text_not_empty(title, 'Risk title')

    if len(title) > MAX_RISK_TITLE_LENGTH:
        raise ValueError(
            f"Risk title is too long. "
            f"Maximum {MAX_RISK_TITLE_LENGTH} characters allowed."
        )
    return title


def validate_flagged_text(text):
    """
    Validates flagged text:
    - Must not be empty
    - Maximum 10,000 characters
    """
    text = validate_text_not_empty(text, 'Flagged text')

    if len(text) > MAX_FLAGGED_TEXT_LENGTH:
        raise ValueError(
            f"Flagged text is too long. "
            f"Maximum {MAX_FLAGGED_TEXT_LENGTH} characters allowed."
        )
    return text


# ============================================================
# OTHER VALIDATORS
# ============================================================

def validate_ordering(ordering):
    """
    Validates ordering parameter.
    Returns default ordering if invalid value given.
    Never raises exception — just falls back to default.
    """
    if ordering not in ALLOWED_ORDERINGS:
        return '-uploaded_at'
    return ordering


def validate_date_format(date_string):
    """
    Validates date string is in YYYY-MM-DD format.
    Raises ValueError with clear message if invalid.
    """
    if not date_string:
        return date_string

    try:
        datetime.strptime(str(date_string), '%Y-%m-%d')
    except ValueError:
        raise ValueError(
            f"'{date_string}' is not a valid date. "
            f"Use format: YYYY-MM-DD (e.g. 2024-01-31)"
        )
    return date_string


def validate_page_size(page_size, max_size=50):
    """
    Validates pagination page_size parameter.
    Returns valid integer or default of 10.
    Never raises exception.
    """
    try:
        size = int(page_size)
        if size < 1:
            return 10
        if size > max_size:
            return max_size
        return size
    except (TypeError, ValueError):
        return 10


def sanitize_search_query(query):
    """
    Sanitizes search query string.
    - Strips whitespace
    - Removes SQL injection attempts
    - Limits length to 200 characters
    Returns sanitized string or empty string.
    """
    if not query or not isinstance(query, str):
        return ''

    # Strip whitespace
    query = query.strip()

    # Limit length
    if len(query) > 200:
        query = query[:200]

    return query