from rest_framework import status
from rest_framework.response import Response


def api_response(success, message, data=None, errors=None, status_code=status.HTTP_200_OK):
    return Response(
        {
            'success': success,
            'message': message,
            'data': data if data is not None else {},
            'errors': errors if errors is not None else {},
        },
        status=status_code,
    )


def api_success(message='تم تنفيذ الطلب بنجاح', data=None, status_code=status.HTTP_200_OK):
    return api_response(
        success=True,
        message=message,
        data=data,
        errors={},
        status_code=status_code,
    )


def api_error(message='فشل تنفيذ الطلب', errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    return api_response(
        success=False,
        message=message,
        data={},
        errors=errors,
        status_code=status_code,
    )
