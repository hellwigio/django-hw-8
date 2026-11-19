from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class AuthenticatedAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(get_user_model().objects.create_user(username="api-test"))
