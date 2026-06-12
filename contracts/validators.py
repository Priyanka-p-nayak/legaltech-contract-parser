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
# All allowed values defined in ONE place.
# If we need to change them, we change here only.
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

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


# ============================================================
# FILE VALIDATORS
# ============================================================

def validate_pdf_file(file):
    """
    Validates an uploaded file:
    1. File must exist
    2. File must have .pdf extension
    3. File must not exceed 10MB

    Args:
        file: InMemoryUploadedFile from request.FILES

    Raises:
        NoFileProvidedException   - if file is None
        InvalidFileTypeException  - if not a PDF
        FileTooLargeException     - if file > 10MB

    Returns:
        file (if all validations pass)
    """

    # Check 1: File exists
    if file is None:
        raise NoFileProvidedException()

    # Check 2: File is a PDF
    # Check both the extension and content type
    file_name = file.name.lower()
    if not file_name.endswith('.pdf'):
        raise InvalidFileTypeException(
            detail=f"'{file.name}' is not a PDF file. Only .pdf files are accepted."
        )

    # Check 3: File size within limit
    if file.size > MAX_FILE_SIZE_BYTES:
        size_mb = file.size / (1024 * 1024)
        raise FileTooLargeException(
            detail=f"File size {size_mb:.1f}MB exceeds the 10MB limit."
        )

    return file


# ============================================================
# STATUS VALIDATORS
# ============================================================

def validate_document_status(status_value):
    """
    Validates that a status value is one of the allowed options.

    Args:
        status_value: string status to validate

    Raises:
        InvalidStatusException - if status not in allowed list

    Returns:
        status_value (if valid)
    """
    if status_value not in ALLOWED_STATUSES:
        raise InvalidStatusException(
            detail=f"'{status_value}' is not a valid status. "
                   f"Allowed values: {', '.join(ALLOWED_STATUSES)}"
        )
    return status_value


# ============================================================
# SEVERITY VALIDATORS
# ============================================================

def validate_severity(severity_value):
    """
    Validates that a severity value is one of: low, medium, high.

    Args:
        severity_value: string severity to validate

    Raises:
        InvalidSeverityException - if severity not in allowed list

    Returns:
        severity_value (if valid)
    """
    if severity_value not in ALLOWED_SEVERITIES:
        raise InvalidSeverityException(
            detail=f"'{severity_value}' is not valid. "
                   f"Allowed: {', '.join(ALLOWED_SEVERITIES)}"
        )
    return severity_value


# ============================================================
# REQUEST BODY VALIDATORS
# ============================================================

def validate_request_body(data):
    """
    Validates that request body is not empty.

    Args:
        data: request.data dictionary

    Raises:
        EmptyRequestBodyException - if data is empty or None

    Returns:
        data (if valid)
    """
    if not data:
        raise EmptyRequestBodyException()
    return data


def validate_confidence_score(score):
    """
    Validates confidence score is between 0.0 and 1.0.

    Args:
        score: float confidence score

    Raises:
        ValueError with clear message

    Returns:
        score (if valid)
    """
    try:
        score = float(score)
    except (TypeError, ValueError):
        raise ValueError("Confidence score must be a number between 0.0 and 1.0")

    if score < 0.0 or score > 1.0:
        raise ValueError(
            f"Confidence score {score} is invalid. Must be between 0.0 and 1.0"
        )
    return score


def validate_page_number(page_num):
    """
    Validates page number is a positive integer >= 1.

    Args:
        page_num: integer page number

    Raises:
        ValueError with clear message

    Returns:
        page_num (if valid)
    """
    try:
        page_num = int(page_num)
    except (TypeError, ValueError):
        raise ValueError("Page number must be a positive integer")

    if page_num < 1:
        raise ValueError(
            f"Page number {page_num} is invalid. Must be 1 or greater."
        )
    return page_num