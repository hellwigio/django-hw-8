from datetime import timedelta
from secrets import token_urlsafe

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from core.models import Task


class JWTApiTests(APITestCase):
    def test_token_refresh_permissions_and_cursor_pages(self):
        password = token_urlsafe()
        user = get_user_model().objects.create_user(username="jwt-test", password=password)
        url = reverse("api:task-list")
        payload = {"title": "New task", "description": "Created with a refreshed access token", "status": "new",
                   "deadline": (timezone.now() + timedelta(days=1)).isoformat()}

        self.assertEqual(self.client.get(url).status_code, 401)
        self.assertEqual(self.client.post(url, payload, format="json").status_code, 401)

        token_url = reverse("api:token-obtain-pair")
        self.assertEqual(self.client.post(token_url, {
            "username": user.username, "password": "incorrect",
        }).status_code, 401)
        tokens = self.client.post(token_url, {"username": user.username, "password": password})
        self.assertEqual(tokens.status_code, 200)
        refreshed = self.client.post(reverse("api:token-refresh"), {"refresh": tokens.data["refresh"]})
        self.assertEqual(refreshed.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refreshed.data['access']}")
        self.assertEqual(self.client.post(url, payload, format="json").status_code, 201)

        for index in range(6):
            Task.objects.create(title=f"Task {index}", deadline=timezone.now())
        first = self.client.get(url)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(len(first.data["results"]), 5)
        second = self.client.get(first.data["next"])
        self.assertEqual(second.status_code, 200)
        self.assertEqual(len(second.data["results"]), 2)
        ids = [item["id"] for page in (first, second) for item in page.data["results"]]
        self.assertEqual(len(set(ids)), 7)
        self.assertIsNone(second.data["next"])
