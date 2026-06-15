import os
from .exceptions import (
    InvalidFileTypeException,
    FileTooLargeException,
    NoFileProvidedException,
    InvalidStatusException,
    InvalidSeverityException,
    EmptyRequestBodyException,
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

ALLOWED_CONTRACT_TYPES = [
    'NDA',
    'MSA',
    'Employment',
    'Service Agreement',
    'Lease',
    'Partnership',
    'Other',
]

ALLOWED_ORDERINGS = [
    'uploaded_at',
    '-uploaded_at',
    'risk_score',
    '-risk_score',
]

# 10 MB in bytes
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Allowed file extensions
ALLOWED_EXTENSIONS = ['.pdf']


# ============================================================
# FILE VALIDATORS
# ============================================================

def validate_pdf_file(file):
    """
    Validates uploaded file:
    1. File must exist
    2. Must be .pdf
    3. Must not exceed 10MB

    Raises custom exceptions with clear messages.
    Returns file if valid.
    """

    # Check 1: File exists
    if file is None:
        raise NoFileProvidedException()

    # Check 2: Extension is .pdf
    file_name  = file.name.lower()
    _, ext     = os.path.splitext(file_name)

    if ext not in ALLOWED_EXTENSIONS:
        raise InvalidFileTypeException(
            detail=(
                f"'{file.name}' is not allowed. "
                f"Only PDF files are accepted."
            )
        )

    # Check 3: File size
    if file.size > MAX_FILE_SIZE_BYTES:
        size_mb = file.size / (1024 * 1024)
        raise FileTooLargeException(
            detail=(
                f"File size {size_mb:.1f}MB exceeds "
                f"the 10MB limit."
            )
        )

    return file


# ============================================================
# STATUS VALIDATORS
# ============================================================

def validate_document_status(status_value):
    """
    Validates status is one of allowed values.
    Raises InvalidStatusException if not valid.
    """
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
    Validates request body is not empty.
    Raises EmptyRequestBodyException if empty.
    """
    if not data:
        raise EmptyRequestBodyException()
    return data


def validate_confidence_score(score):
    """
    Validates confidence score is float between 0.0 and 1.0.
    Raises ValueError with clear message if invalid.
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
    return score


def validate_page_number(page_num):
    """
    Validates page number is positive integer >= 1.
    Raises ValueError with clear message if invalid.
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
    return page_num


def validate_risk_score(score):
    """
    Validates risk score is non-negative integer.
    Raises ValueError if invalid.
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
    return score


def validate_ordering(ordering):
    """
    Validates ordering parameter is allowed.
    Returns default ordering if invalid.
    """
    if ordering not in ALLOWED_ORDERINGS:
        return '-uploaded_at'
    return ordering


def validate_date_format(date_string):
    """
    Validates date string is in YYYY-MM-DD format.
    Raises ValueError if invalid.
    """
    from datetime import datetime
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
    except ValueError:
        raise ValueError(
            f"'{date_string}' is not a valid date. "
            f"Use format: YYYY-MM-DD (e.g. 2024-01-31)"
        )
    return date_string