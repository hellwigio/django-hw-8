from rest_framework_simplejwt.tokens import AccessToken, BlacklistMixin


class RevocableAccessToken(BlacklistMixin, AccessToken):
    pass
