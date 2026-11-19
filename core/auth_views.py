from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.middleware.csrf import get_token, rotate_token
from rest_framework import generics, serializers, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .authentication import ACCESS_COOKIE, REFRESH_COOKIE
from .models import RegisteredEmail
from .tokens import RevocableAccessToken


User = get_user_model()
COOKIE_PATHS = {ACCESS_COOKIE: "/api/", REFRESH_COOKIE: "/api/auth/"}


class RegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email address is already registered.")
        return value

    def validate(self, attrs):
        user = User(username=attrs["username"], email=attrs["email"])
        try:
            validate_password(attrs["password"], user=user)
        except DjangoValidationError as error:
            raise serializers.ValidationError({"password": error.messages}) from error
        return attrs

    def create(self, validated_data):
        try:
            with transaction.atomic():
                user = User.objects.create_user(**validated_data)
                RegisteredEmail.objects.create(address=user.email, user=user)
                return user
        except IntegrityError as error:
            if User.objects.filter(username=validated_data["username"]).exists():
                raise serializers.ValidationError({"username": "This username is already registered."}) from error
            if RegisteredEmail.objects.filter(address=validated_data["email"]).exists():
                raise serializers.ValidationError({"email": "This email address is already registered."}) from error
            raise


class RegisterView(generics.CreateAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer


class CsrfView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"csrfToken": get_token(request)})


def set_jwt_cookies(response):
    for key, name, lifetime in (
        ("access", ACCESS_COOKIE, api_settings.ACCESS_TOKEN_LIFETIME),
        ("refresh", REFRESH_COOKIE, api_settings.REFRESH_TOKEN_LIFETIME),
    ):
        if key in response.data:
            response.set_cookie(
                name, response.data.pop(key), max_age=int(lifetime.total_seconds()),
                path=COOKIE_PATHS[name], secure=True, httponly=True, samesite="Lax",
            )
    response["Cache-Control"] = "no-store"
    return response


class CookieLoginView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        SessionAuthentication().enforce_csrf(request)
        response = super().post(request, *args, **kwargs)
        rotate_token(request)
        response.data["csrfToken"] = get_token(request)
        return set_jwt_cookies(response)


class CookieRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        SessionAuthentication().enforce_csrf(request)
        serializer = self.get_serializer(data={"refresh": request.COOKIES.get(REFRESH_COOKIE)})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as error:
            raise InvalidToken(error.args[0]) from error
        return set_jwt_cookies(Response(serializer.validated_data))


class CookieLogoutView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        SessionAuthentication().enforce_csrf(request)
        with transaction.atomic():
            for name, token_class in ((ACCESS_COOKIE, RevocableAccessToken), (REFRESH_COOKIE, RefreshToken)):
                raw_token = request.COOKIES.get(name)
                if raw_token:
                    try:
                        token = token_class(raw_token)
                    except TokenError:
                        continue
                    token.blacklist()

        response = Response(status=status.HTTP_204_NO_CONTENT)
        response["Cache-Control"] = "no-store"
        for name, path in COOKIE_PATHS.items():
            response.delete_cookie(name, path=path, samesite="Lax")
        return response
