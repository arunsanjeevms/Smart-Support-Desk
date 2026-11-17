"""
A single error format for the whole API so the Angular app can show helpful
messages without guessing the shape of the response:

    {"message": "Please correct the highlighted fields.",
     "errors": {"title": ["This field is required."]}}
"""

from rest_framework import exceptions, status
from rest_framework.views import exception_handler


def _first_message(errors):
    if isinstance(errors, list) and errors:
        return _first_message(errors[0])
    if isinstance(errors, dict) and errors:
        return _first_message(next(iter(errors.values())))
    return str(errors)


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None  # unexpected error: let Django return a 500

    data = response.data
    if isinstance(exc, exceptions.ValidationError):
        errors = data if isinstance(data, dict) else {"non_field_errors": data}
        non_field = errors.get("non_field_errors")
        message = (
            _first_message(non_field) if non_field else "Please correct the highlighted fields."
        )
        response.data = {"message": message, "errors": errors}
    else:
        detail = data.get("detail") if isinstance(data, dict) else data
        response.data = {"message": str(detail) if detail else "Request failed.", "errors": {}}

    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        response.data["message"] = "Your session has expired. Please sign in again."
    return response
