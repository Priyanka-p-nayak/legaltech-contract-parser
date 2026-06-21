"""
exceptions.py
=============
Custom exception classes for the LegalTech API.

Each exception bundles together an HTTP status code, a
machine-readable error_code, and a clear human message —
so raising `InvalidFileTypeException()` anywhere in the
codebase automatically produces a consistent error response
via error_handlers.py's custom_exception_handler.

Full status code + error code reference: docs/STATUS_CODES.md
"""

from rest_framework.exceptions import APIException
from rest_framework import status


# ============================================================
# CUSTOM EXCEPTION CLASSES
#
# Each exception:
# 1. Has a specific HTTP status code
# 2. Has a machine-readable error_code
# 3. Has a clear human-readable message
# 4. Can accept a custom detail message
# ============================================================


class DocumentNotFoundException(APIException):
    """
    Raised when a document with given ID does not exist.

    HTTP Status : 404 Not Found
    Error Code  : DOCUMENT_NOT_FOUND
    When        : GET/PATCH/POST on /documents/{id}/ with bad ID
    """
    status_code   = status.HTTP_404_NOT_FOUND
    default_detail = "Document not found. Please check the document ID."
    default_code   = "DOCUMENT_NOT_FOUND"


class InvalidFileTypeException(APIException):
    """
    Raised when uploaded file is not a PDF.

    HTTP Status : 400 Bad Request
    Error Code  : INVALID_FILE_TYPE
    When        : POST /documents/upload/ with non-PDF file
    """
    status_code    = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "Invalid file type. Only PDF files (.pdf) are accepted. "
        "Please upload a valid PDF document."
    )
    default_code = "INVALID_FILE_TYPE"


class FileTooLargeException(APIException):
    """
    Raised when uploaded file exceeds the size limit.

    HTTP Status : 413 Payload Too Large
    Error Code  : FILE_TOO_LARGE
    When        : POST /documents/upload/ with file > 10MB
    """
    status_code    = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    default_detail = (
        "File too large. Maximum allowed size is 10MB. "
        "Please compress your PDF or split it into smaller files."
    )
    default_code = "FILE_TOO_LARGE"


class EmptyFileException(APIException):
    """
    Raised when uploaded file is empty (0 bytes).

    HTTP Status : 400 Bad Request
    Error Code  : EMPTY_FILE
    When        : POST /documents/upload/ with 0 byte file
    """
    status_code    = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "File is empty (0 bytes). "
        "Please upload a valid PDF with content."
    )
    default_code = "EMPTY_FILE"


class NoFileProvidedException(APIException):
    """
    Raised when upload request has no file attached.

    HTTP Status : 400 Bad Request
    Error Code  : NO_FILE_PROVIDED
    When        : POST /documents/upload/ with no file key
    """
    status_code    = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "No file provided. "
        "Please attach a PDF file using the 'file' field."
    )
    default_code = "NO_FILE_PROVIDED"


class InvalidStatusException(APIException):
    """
    Raised when an invalid status value is provided.

    HTTP Status : 400 Bad Request
    Error Code  : INVALID_STATUS
    When        : PATCH /documents/{id}/update-status/ with bad status
    Allowed     : uploaded, processing, completed, failed
    """
    status_code    = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "Invalid status value. "
        "Allowed values: uploaded, processing, completed, failed."
    )
    default_code = "INVALID_STATUS"


class InvalidSeverityException(APIException):
    """
    Raised when an invalid severity value is provided.

    HTTP Status : 400 Bad Request
    Error Code  : INVALID_SEVERITY
    When        : POST /documents/{id}/risks/ with bad severity
    Allowed     : low, medium, high
    """
    status_code    = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "Invalid severity value. "
        "Allowed values: low, medium, high."
    )
    default_code = "INVALID_SEVERITY"


class EmptyRequestBodyException(APIException):
    """
    Raised when request body is empty or missing.

    HTTP Status : 400 Bad Request
    Error Code  : EMPTY_REQUEST_BODY
    When        : PATCH/POST with no body or empty {}
    """
    status_code    = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "Request body is empty. "
        "Please provide the required data in the request body."
    )
    default_code = "EMPTY_REQUEST_BODY"


class BulkLimitExceededException(APIException):
    """
    Raised when bulk request exceeds the allowed limit.

    HTTP Status : 400 Bad Request
    Error Code  : BULK_LIMIT_EXCEEDED
    When        : POST with list of more than 100 items
    """
    status_code    = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "Bulk request limit exceeded. "
        "Maximum 100 items allowed per request. "
        "Please split your request into smaller batches."
    )
    default_code = "BULK_LIMIT_EXCEEDED"


class DocumentAlreadyProcessedException(APIException):
    """
    Raised when trying to re-process an already completed document.

    HTTP Status : 409 Conflict
    Error Code  : DOCUMENT_ALREADY_PROCESSED
    When        : POST /nlp/documents/{id}/process/ on completed doc

    WHY 409 and not 400: the request itself is well-formed —
    the conflict is with the SERVER's current state, not with
    anything wrong in the request body. See docs/STATUS_CODES.md.
    """
    status_code    = status.HTTP_409_CONFLICT
    default_detail = (
        "This document has already been processed. "
        "Cannot re-process a completed document. "
        "Use the update-status endpoint to make changes."
    )
    default_code = "DOCUMENT_ALREADY_PROCESSED"


class InvalidDateFormatException(APIException):
    """
    Raised when a date field is not in YYYY-MM-DD format.

    HTTP Status : 400 Bad Request
    Error Code  : INVALID_DATE_FORMAT
    When        : Any endpoint with date fields
    """
    status_code    = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "Invalid date format. "
        "Please use YYYY-MM-DD format (e.g. 2024-01-31)."
    )
    default_code = "INVALID_DATE_FORMAT"


class DatabaseOperationException(APIException):
    """
    Raised when a database operation fails unexpectedly.

    HTTP Status : 500 Internal Server Error
    Error Code  : DATABASE_ERROR
    When        : Any unexpected DB failure
    """
    status_code    = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = (
        "A database error occurred. "
        "Please try again. "
        "If the problem persists, contact support."
    )
    default_code = "DATABASE_ERROR"


class ValidationException(APIException):
    """
    Generic validation exception for field-level errors.

    HTTP Status : 400 Bad Request
    Error Code  : VALIDATION_ERROR
    When        : Any field validation failure
    """
    status_code    = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "Validation failed. "
        "Please check the provided data and try again."
    )
    default_code = "VALIDATION_ERROR"