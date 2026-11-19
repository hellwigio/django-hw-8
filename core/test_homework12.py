from datetime import timedelta
from uuid import uuid4

from django.urls import reverse
from django.utils import timezone
from core.api_test_helpers import AuthenticatedAPITestCase

from core.models import Task


class TaskApiTests(AuthenticatedAPITestCase):
    def payload(self, **changes):
        return {
            "title": "API task", "description": "Created via API", "status": "new",
            "deadline": (timezone.now() + timedelta(days=3)).isoformat(), **changes,
        }

    def test_create_list_and_detail(self):
        response = self.client.post(reverse("api:task-create"), self.payload(), format="json")
        self.assertEqual(response.status_code, 201)
        task = Task.objects.get(pk=response.data["id"])
        self.assertEqual(task.description, "Created via API")
        response = self.client.get(reverse("api:task-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], str(task.pk))
        response = self.client.get(reverse("api:task-detail", args=[task.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], task.title)

    def test_invalid_payloads_and_duplicate_title(self):
        self.client.post(reverse("api:task-create"), self.payload(), format="json")
        for payload in ({}, self.payload(), self.payload(title="Other", status="invalid"),
                        self.payload(title="Other", deadline="not-a-date")):
            response = self.client.post(reverse("api:task-create"), payload, format="json")
            self.assertEqual(response.status_code, 400)
        self.assertEqual(Task.objects.count(), 1)

    def test_missing_task_and_unsupported_method(self):
        self.assertEqual(self.client.get(reverse("api:task-detail", args=[uuid4()])).status_code, 404)
        self.assertEqual(self.client.get(reverse("api:task-create")).status_code, 405)

    def test_empty_statistics(self):
        response = self.client.get(reverse("api:task-statistics"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            "total": 0, "by_status": dict.fromkeys(Task.Status.values, 0), "overdue": 0,
        })

    def test_statistics_count_every_status_and_expired_deadlines(self):
        now = timezone.now()
        for index, task_status in enumerate(Task.Status.values):
            Task.objects.create(title=f"Task {index}", description="Stats", status=task_status,
                                deadline=now + timedelta(days=1 if index == 0 else -1))
        response = self.client.get(reverse("api:task-statistics"))
        self.assertEqual(response.data, {
            "total": 5, "by_status": dict.fromkeys(Task.Status.values, 1), "overdue": 4,
        })
