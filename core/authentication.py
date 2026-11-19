from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication


ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        if self.get_header(request) is not None:
            return super().authenticate(request)

        raw_token = request.COOKIES.get(ACCESS_COOKIE)
        if not raw_token:
            return None

        token = self.get_validated_token(raw_token)
        user = self.get_user(token)
        SessionAuthentication().enforce_csrf(request)
        return user, token
