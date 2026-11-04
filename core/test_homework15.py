from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from core.models import SubTask, Task


class Homework15Tests(APITestCase):
    def test_task_full_crud_through_generic_views(self):
        payload = {"title": "Generic task", "description": "Create", "status": "new",
                   "deadline": (timezone.now() + timedelta(days=2)).isoformat()}
        response = self.client.post(reverse("api:task-list"), payload, format="json")
        self.assertEqual(response.status_code, 201)
        pk = response.data["id"]
        detail = reverse("api:task-detail", args=[pk])
        self.assertEqual(self.client.get(detail).status_code, 200)
        response = self.client.put(detail, {**payload, "description": "Full update"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["description"], "Full update")
        self.assertEqual(self.client.patch(detail, {"status": "done"}, format="json").status_code, 200)
        self.assertEqual(Task.objects.get(pk=pk).status, "done")
        self.assertEqual(self.client.delete(detail).status_code, 204)
        self.assertEqual(self.client.get(detail).status_code, 404)

    def test_filters_search_ordering_for_tasks_and_subtasks(self):
        now = timezone.now()
        deadline = now + timedelta(days=3)
        parent = Task.objects.create(title="Parent", description="Parent", deadline=deadline)
        for model, endpoint in ((Task, "api:task-list"), (SubTask, "api:subtask-list-create")):
            with self.subTest(model=model.__name__):
                extra = {"task": parent} if model is SubTask else {}
                first = model.objects.create(title=f"Alpha {model.__name__}", description="Needle text",
                                             status="new", deadline=deadline, **extra)
                second = model.objects.create(title=f"Beta {model.__name__}", description="Other text",
                                              status="done", deadline=deadline + timedelta(days=1), **extra)
                model.objects.filter(pk=first.pk).update(created_at=now - timedelta(days=1))
                model.objects.filter(pk=second.pk).update(created_at=now)
                url = reverse(endpoint)

                def rows(params):
                    response = self.client.get(url, params)
                    self.assertEqual(response.status_code, 200)
                    return response.data["results"] if model is SubTask else response.data

                self.assertEqual([r["id"] for r in rows({"search": "Alpha"})], [str(first.pk)])
                self.assertEqual([r["id"] for r in rows({"search": "Needle"})], [str(first.pk)])
                self.assertEqual([r["id"] for r in rows({"status": "done", "search": model.__name__})], [str(second.pk)])
                self.assertEqual([r["id"] for r in rows({"deadline": deadline.isoformat(), "search": model.__name__})], [str(first.pk)])
                self.assertEqual([r["id"] for r in rows({"ordering": "created_at", "search": model.__name__})], [str(first.pk), str(second.pk)])
                self.assertEqual([r["id"] for r in rows({"ordering": "-created_at", "search": model.__name__})], [str(second.pk), str(first.pk)])
                self.assertEqual(self.client.get(url, {"deadline": "invalid"}).status_code, 400)
