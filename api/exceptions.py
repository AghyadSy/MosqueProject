from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.views import exception_handler

from .responses import api_error, api_success
import traceback

def _flatten_error_detail(value):
    if isinstance(value, dict):
        return {key: _flatten_error_detail(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_flatten_error_detail(item) for item in value]
    if isinstance(value, ErrorDetail):
        return str(value)
    return value


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)


    if response is None:
        print("🔥 UNHANDLED EXCEPTION:")
        traceback.print_exc()

        return api_error(
            message=str(exc),   # 👈 مهم جداً يظهر الخطأ الحقيقي
            errors={
                'detail': str(exc),
                'type': str(type(exc).__name__)
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    if response.status_code == status.HTTP_404_NOT_FOUND:
        return api_success(
            message='لا توجد بيانات',
            data={},
            status_code=status.HTTP_200_OK,
        )

    errors = _flatten_error_detail(response.data)
    message = 'فشل تنفيذ الطلب'

    if isinstance(errors, dict):
        detail = errors.get('detail')
        if isinstance(detail, str):
            message = detail
        elif detail:
            message = 'فشل تنفيذ الطلب'
    elif isinstance(errors, list) and errors:
        message = str(errors[0])

    if response.status_code == status.HTTP_401_UNAUTHORIZED and message == 'فشل تنفيذ الطلب':
        message = 'يجب تسجيل الدخول للوصول إلى هذا المسار'
    elif response.status_code == status.HTTP_403_FORBIDDEN and message == 'فشل تنفيذ الطلب':
        message = 'لا تملك صلاحية تنفيذ هذا الإجراء'
    elif response.status_code == status.HTTP_404_NOT_FOUND and message == 'فشل تنفيذ الطلب':
        message = 'العنصر المطلوب غير موجود'

    return api_error(
        message=message,
        errors=errors if isinstance(errors, dict) else {'detail': errors},
        status_code=response.status_code,
    )
