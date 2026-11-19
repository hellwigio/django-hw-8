from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken


class OwnershipApiTests(APITestCase):
    def authenticate(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")

    def test_owner_is_taken_from_token_and_only_owner_can_write(self):
        users = get_user_model().objects
        owner = users.create_user(username="owner")
        other = users.create_user(username="other")
        self.authenticate(owner)
        payload = {
            "title": "Owned task", "description": "Example", "owner": other.pk,
            "deadline": (timezone.now() + timedelta(days=1)).isoformat(),
        }
        task = self.client.post(reverse("api:task-list"), payload, format="json")
        self.assertEqual(task.status_code, 201)
        self.assertEqual(task.data["owner"], owner.pk)
        subtask = self.client.post(reverse("api:subtask-list-create"), {
            **payload, "title": "Owned subtask", "task": task.data["id"],
        }, format="json")
        self.assertEqual(subtask.status_code, 201)
        self.assertEqual(subtask.data["owner"], owner.pk)
        mine = reverse("api:task-mine")
        self.assertEqual([r["id"] for r in self.client.get(mine).data["results"]], [task.data["id"]])

        for route, item in (("api:task-detail", task), ("api:subtask-detail", subtask)):
            url = reverse(route, args=[item.data["id"]])
            self.authenticate(other)
            self.assertEqual(self.client.get(mine).data["results"], [])
            self.assertEqual(self.client.get(url).status_code, 200)
            self.assertEqual(self.client.patch(url, {"status": "done"}).status_code, 403)
            self.assertEqual(self.client.delete(url).status_code, 403)
            self.authenticate(owner)
            response = self.client.patch(url, {"status": "done", "owner": other.pk})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["owner"], owner.pk)
        self.assertEqual(self.client.delete(reverse("api:subtask-detail", args=[subtask.data["id"]])).status_code, 204)
        self.assertEqual(self.client.delete(reverse("api:task-detail", args=[task.data["id"]])).status_code, 204)

    def test_documentation_routes_and_bearer_schema(self):
        self.assertEqual(self.client.get(reverse("swagger")).status_code, 200)
        self.assertEqual(self.client.get(reverse("redoc")).status_code, 200)
        response = self.client.get(reverse("swagger-schema"), HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 200)
        schema = response.json()
        self.assertEqual(schema["securityDefinitions"]["Bearer"]["name"], "Authorization")
        self.assertIn("/tasks/mine/", schema["paths"])
