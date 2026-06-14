from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


# ============================================================
# CUSTOM EXCEPTION HANDLER
# This function is called automatically by Django REST
# Framework whenever ANY exception occurs in ANY view.
# It formats ALL errors into our standard JSON structure.
# ============================================================

def custom_exception_handler(exc, context):
    """
    Global exception handler for all API errors.

    Catches every exception and returns a clean JSON response:
    {
        "success": false,
        "message": "Human readable message",
        "error_code": "MACHINE_READABLE_CODE",
        "errors": { detailed errors if any }
    }

    Args:
        exc     : The exception that was raised
        context : Dict with request and view info
    """

    # First let DRF handle it (converts to Response if possible)
    response = exception_handler(exc, context)

    # ── DRF handled it (4xx errors) ────────────────────────
    if response is not None:
        error_data = {
            "success": False,
            "message": _get_error_message(response.data),
            "status_code": response.status_code,
        }

        # Include error code if present
        if hasattr(exc, 'default_code'):
            error_data["error_code"] = exc.default_code

        # Include detailed field errors for validation failures
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            if isinstance(response.data, dict):
                error_data["errors"] = response.data

        response.data = error_data
        return response

    # ── Unhandled exceptions (500 errors) ──────────────────
    # These are unexpected server errors
    return Response(
        {
            "success": False,
            "message": "An unexpected server error occurred. Please try again.",
            "error_code": "INTERNAL_SERVER_ERROR",
            "status_code": 500,
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def _get_error_message(data):
    """
    Extract a clean human-readable message from error data.

    DRF returns errors in many different formats.
    This function normalizes them all into one string.
    """

    # If data has a 'detail' key (most DRF errors)
    if isinstance(data, dict):
        if 'detail' in data:
            detail = data['detail']
            # detail can be a string or ErrorDetail object
            return str(detail)

        # If data has field errors, list them
        messages = []
        for field, errors in data.items():
            if isinstance(errors, list):
                for error in errors:
                    messages.append(f"{field}: {str(error)}")
            else:
                messages.append(f"{field}: {str(errors)}")
        return " | ".join(messages) if messages else "Validation failed."

    # If data is a list
    if isinstance(data, list):
        return " | ".join([str(item) for item in data])

    return str(data)