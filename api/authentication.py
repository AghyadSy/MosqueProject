from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header

from .models import ApiAccessToken


class ApiTokenAuthentication(BaseAuthentication):
    keyword = 'Bearer'

    def authenticate(self, request):
        raw_header = get_authorization_header(request).decode('utf-8')
        token_key = None

        if raw_header:
            parts = raw_header.split()
            if len(parts) != 2 or parts[0] != self.keyword:
                raise exceptions.AuthenticationFailed('صيغة Authorization غير صحيحة')
            token_key = parts[1]
        else:
            token_key = request.headers.get('X-API-Token')

        if not token_key:
            return None

        token = ApiAccessToken.objects.select_related('user').filter(key=token_key).first()
        if token is None:
            raise exceptions.AuthenticationFailed('رمز الدخول غير صالح')

        token.touch()
        return (token.user, token)

    def authenticate_header(self, request):
        return self.keyword
