"""Standard error envelope for all API error responses (skill contract):

{"success": false, "message": "...", "errors": {...}}
"""

from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return response

    errors = response.data if isinstance(response.data, dict) else {'detail': response.data}
    message = errors.pop('detail', None) or 'Unable to process request'

    response.data = {
        'success': False,
        'message': message,
        'errors': errors,
    }
    return response
