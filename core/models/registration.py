from django.conf import settings
from django.db import models


class RegisteredEmail(models.Model):
    """Reserve normalized email addresses for API registrations."""

    address = models.EmailField(unique=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
