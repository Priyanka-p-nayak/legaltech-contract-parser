from rest_framework.exceptions import APIException
from rest_framework import status


# ============================================================
# CUSTOM EXCEPTION CLASSES
# These are our own error types that we raise in views
# when something goes wrong.
# Each one automatically returns a clean JSON error response.
# ============================================================


class DocumentNotFoundException(APIException):
    """
    Raised when a document with given ID is not found.
    Returns: 404 Not Found
    """
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Document not found."
    default_code = "DOCUMENT_NOT_FOUND"


class InvalidFileTypeException(APIException):
    """
    Raised when uploaded file is not a PDF.
    Returns: 400 Bad Request
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid file type. Only PDF files are allowed."
    default_code = "INVALID_FILE_TYPE"


class FileTooLargeException(APIException):
    """
    Raised when uploaded file exceeds size limit.
    Returns: 400 Bad Request
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "File too large. Maximum allowed size is 10MB."
    default_code = "FILE_TOO_LARGE"


class NoFileProvidedException(APIException):
    """
    Raised when upload request has no file attached.
    Returns: 400 Bad Request
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "No file provided. Please attach a PDF file."
    default_code = "NO_FILE_PROVIDED"


class InvalidStatusException(APIException):
    """
    Raised when an invalid status value is provided.
    Returns: 400 Bad Request
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid status value provided."
    default_code = "INVALID_STATUS"


class InvalidSeverityException(APIException):
    """
    Raised when an invalid severity value is provided.
    Returns: 400 Bad Request
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid severity. Allowed values: low, medium, high."
    default_code = "INVALID_SEVERITY"


class EmptyRequestBodyException(APIException):
    """
    Raised when request body is empty or missing.
    Returns: 400 Bad Request
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Request body is empty. Please provide required data."
    default_code = "EMPTY_REQUEST_BODY"


class DatabaseOperationException(APIException):
    """
    Raised when a database operation fails unexpectedly.
    Returns: 500 Internal Server Error
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "A database error occurred. Please try again."
    default_code = "DATABASE_ERROR"