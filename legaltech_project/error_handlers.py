from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

# Get logger for error tracking
logger = logging.getLogger(__name__)


# ============================================================
# CUSTOM EXCEPTION HANDLER
#
# Called automatically by DRF whenever ANY exception
# occurs in ANY view across the entire project.
#
# Ensures ALL errors return the same clean JSON structure:
# {
#     "success":     false,
#     "message":     "Human readable message",
#     "error_code":  "MACHINE_READABLE_CODE",
#     "status_code": 400,
#     "errors":      { field-level errors if any }
# }
# ============================================================

def custom_exception_handler(exc, context):
    """
    Global exception handler for all API errors.

    Args:
        exc     : The exception that was raised
        context : Dict with request, view, args, kwargs

    Returns:
        Response with standard error format
    """

    # Step 1: Let DRF handle it first
    # This converts known exceptions to Response objects
    response = exception_handler(exc, context)

    # Step 2: Log the error for debugging
    view    = context.get('view', None)
    request = context.get('request', None)

    if response is not None:
        # Log 5xx errors as ERROR, 4xx as WARNING
        if response.status_code >= 500:
            logger.error(
                f"Server Error: {exc} | "
                f"View: {view.__class__.__name__ if view else 'Unknown'} | "
                f"URL: {request.path if request else 'Unknown'}"
            )
        else:
            logger.warning(
                f"Client Error {response.status_code}: {exc} | "
                f"URL: {request.path if request else 'Unknown'}"
            )

    # Step 3: Handle DRF-handled exceptions (4xx errors)
    if response is not None:

        # Extract clean message from response data
        message = _extract_message(response.data)

        # Build standard error response
        error_data = {
            "success":     False,
            "message":     message,
            "status_code": response.status_code,
        }

        # Add error_code if exception has one
        if hasattr(exc, 'default_code') and exc.default_code:
            error_data["error_code"] = exc.default_code

        # Add field-level errors for 400 validation failures
        if (
            response.status_code == status.HTTP_400_BAD_REQUEST
            and isinstance(response.data, dict)
        ):
            # Filter out the 'detail' key — it's already in message
            field_errors = {
                k: v for k, v in response.data.items()
                if k != 'detail'
            }
            if field_errors:
                error_data["errors"] = field_errors

        response.data = error_data
        return response

    # Step 4: Handle completely unhandled exceptions (500 errors)
    # These are unexpected crashes in our code
    logger.error(
        f"Unhandled Exception: {type(exc).__name__}: {exc} | "
        f"View: {view.__class__.__name__ if view else 'Unknown'}"
    )

    return Response(
        {
            "success":     False,
            "message":     (
                "An unexpected server error occurred. "
                "Please try again later."
            ),
            "error_code":  "INTERNAL_SERVER_ERROR",
            "status_code": 500,
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def _extract_message(data):
    """
    Extract a clean human-readable message from DRF error data.

    DRF returns errors in many different formats depending
    on which exception was raised. This normalizes them all.
    """

    if data is None:
        return "An error occurred."

    # Most DRF exceptions use 'detail' key
    if isinstance(data, dict):
        if 'detail' in data:
            detail = data['detail']
            # detail can be string, list, or ErrorDetail object
            if isinstance(detail, list):
                return str(detail[0]) if detail else "An error occurred."
            return str(detail)

        # Field validation errors — collect them all
        messages = []
        for field, errors in data.items():
            if isinstance(errors, list):
                for error in errors:
                    messages.append(f"{field}: {str(error)}")
            elif isinstance(errors, dict):
                messages.append(f"{field}: validation failed")
            else:
                messages.append(f"{field}: {str(errors)}")

        if messages:
            return " | ".join(messages)
        return "Validation failed."

    # List of error messages
    if isinstance(data, list):
        if data:
            return str(data[0])
        return "An error occurred."

    return str(data)


# ============================================================
# CUSTOM 404 HANDLER
# Called when a URL pattern is not found
# ============================================================

def handler404(request, exception=None):
    """Handle 404 Not Found for invalid URLs."""
    from django.http import JsonResponse
    return JsonResponse(
        {
            "success":     False,
            "message":     (
                f"The URL '{request.path}' was not found. "
                f"Please check the API documentation."
            ),
            "error_code":  "URL_NOT_FOUND",
            "status_code": 404,
        },
        status=404
    )


# ============================================================
# CUSTOM 500 HANDLER
# Called when Django itself crashes
# ============================================================

def handler500(request):
    """Handle 500 Internal Server Error."""
    from django.http import JsonResponse
    return JsonResponse(
        {
            "success":     False,
            "message":     (
                "An internal server error occurred. "
                "Please try again later."
            ),
            "error_code":  "INTERNAL_SERVER_ERROR",
            "status_code": 500,
        },
        status=500
    )