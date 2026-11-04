from datetime import timedelta
from uuid import uuid4

from django.urls import reverse
from django.utils import timezone
from rest_framework import serializers
from rest_framework.test import APITestCase

from core.models import Category, SubTask, Task
from core.serializers import CategoryCreateSerializer


class Homework13Tests(APITestCase):
    def setUp(self):
        self.task = Task.objects.create(title="Parent", description="Parent task",
                                       deadline=timezone.now() + timedelta(days=3))

    def payload(self, **changes):
        return {"title": "Child", "description": "Subtask", "task": str(self.task.pk),
                "status": "new", "deadline": self.task.deadline.isoformat(), **changes}

    def test_subtask_crud_and_read_only_created_at(self):
        url = reverse("api:subtask-list-create")
        response = self.client.post(url, self.payload(created_at="2000-01-01T00:00:00Z"), format="json")
        self.assertEqual(response.status_code, 201)
        child = SubTask.objects.get(pk=response.data["id"])
        self.assertGreater(child.created_at.year, 2000)
        original_created_at = child.created_at
        detail = reverse("api:subtask-detail", args=[child.pk])
        self.assertEqual(self.client.get(url).data[0]["id"], str(child.pk))
        self.assertEqual(self.client.get(detail).status_code, 200)
        response = self.client.put(detail, self.payload(title="Updated", status="in_progress"), format="json")
        self.assertEqual(response.status_code, 200)
        response = self.client.patch(detail, {"status": "done", "created_at": "2001-01-01T00:00:00Z"}, format="json")
        self.assertEqual(response.status_code, 200)
        child.refresh_from_db()
        self.assertEqual(child.status, "done")
        self.assertEqual(child.created_at, original_created_at)
        nested = self.client.get(reverse("api:task-detail", args=[self.task.pk])).data["subtasks"]
        self.assertEqual(nested[0]["title"], "Updated")
        self.assertEqual(nested[0]["description"], "Subtask")
        self.assertEqual(self.client.delete(detail).status_code, 204)
        self.assertFalse(SubTask.objects.filter(pk=child.pk).exists())
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())
        self.assertEqual(self.client.get(detail).status_code, 404)

    def test_invalid_subtask_and_missing_id(self):
        url = reverse("api:subtask-list-create")
        for payload in ({}, self.payload(task=str(uuid4())), self.payload(status="invalid")):
            self.assertEqual(self.client.post(url, payload, format="json").status_code, 400)
        detail = reverse("api:subtask-detail", args=[uuid4()])
        for method in (self.client.get, self.client.put, self.client.patch, self.client.delete):
            self.assertEqual(method(detail).status_code, 404)

    def test_task_deadline_validation_and_empty_nested_list(self):
        payload = {"title": "Past task", "description": "Past", "status": "new",
                   "deadline": (timezone.now() - timedelta(days=1)).isoformat()}
        response = self.client.post(reverse("api:task-create"), payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("deadline", response.data)
        response = self.client.get(reverse("api:task-detail", args=[self.task.pk]))
        self.assertEqual(response.data["subtasks"], [])

    def test_category_create_update_uniqueness(self):
        first = CategoryCreateSerializer(data={"name": "Work"})
        first.is_valid(raise_exception=True)
        category = first.save()
        duplicate = CategoryCreateSerializer(data={"name": "Work"})
        duplicate.is_valid(raise_exception=True)
        with self.assertRaises(serializers.ValidationError):
            duplicate.save()
        other = Category.objects.create(name="Personal")
        duplicate = CategoryCreateSerializer(other, data={"name": "Work"})
        duplicate.is_valid(raise_exception=True)
        with self.assertRaises(serializers.ValidationError):
            duplicate.save()
        unchanged = CategoryCreateSerializer(category, data={"name": "Work"})
        unchanged.is_valid(raise_exception=True)
        self.assertEqual(unchanged.save().name, "Work")
        renamed = CategoryCreateSerializer(category, data={"name": "Office"})
        renamed.is_valid(raise_exception=True)
        self.assertEqual(renamed.save().name, "Office")
