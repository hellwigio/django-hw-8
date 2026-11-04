from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from core.models import Category, Task


class Homework16Tests(APITestCase):
    def test_category_crud_soft_deletes_and_hides_record(self):
        url = reverse("api:category-list")
        response = self.client.post(url, {"name": "Work"}, format="json")
        self.assertEqual(response.status_code, 201)
        pk = response.data["id"]
        detail = reverse("api:category-detail", args=[pk])
        self.assertEqual(self.client.get(detail).status_code, 200)
        self.assertEqual(self.client.put(detail, {"name": "Office"}, format="json").status_code, 200)
        self.assertEqual(self.client.patch(detail, {"name": "Business"}, format="json").status_code, 200)
        category = Category.objects.get(pk=pk)
        task = Task.objects.create(title="Categorized", description="Keep task",
                                   deadline=timezone.now() + timedelta(days=1))
        task.categories.add(category)
        before = timezone.now()
        self.assertEqual(self.client.delete(detail).status_code, 204)
        deleted = Category.all_objects.get(pk=pk)
        self.assertTrue(deleted.is_deleted)
        self.assertGreaterEqual(deleted.deleted_at, before)
        self.assertFalse(Category.objects.filter(pk=pk).exists())
        self.assertEqual(self.client.get(url).data, [])
        self.assertEqual(self.client.get(detail).status_code, 404)
        self.assertEqual(self.client.delete(detail).status_code, 404)
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())
        self.assertTrue(Task.categories.through.objects.filter(category_id=pk, task_id=task.pk).exists())
        # Unique names remain reserved by retained rows, returning validation instead of SQL errors.
        self.assertEqual(self.client.post(url, {"name": "Business"}, format="json").status_code, 400)

    def test_count_tasks_includes_zero_and_excludes_deleted_categories(self):
        first = Category.objects.create(name="First")
        Category.objects.create(name="Empty")
        deleted = Category.objects.create(name="Deleted")
        for index in range(2):
            task = Task.objects.create(title=f"Task {index}", description="Count",
                                       deadline=timezone.now() + timedelta(days=1))
            task.categories.add(first, deleted)
        deleted.delete()
        response = self.client.get(reverse("api:category-count-tasks"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual({r["name"]: r["task_count"] for r in response.data}, {"Empty": 0, "First": 2})

    def test_queryset_delete_is_also_soft(self):
        category = Category.objects.create(name="Bulk")
        count, _ = Category.objects.filter(pk=category.pk).delete()
        self.assertEqual(count, 1)
        self.assertTrue(Category.all_objects.get(pk=category.pk).is_deleted)
        self.assertIsNotNone(Category.all_objects.get(pk=category.pk).deleted_at)

    def test_api_cannot_set_soft_delete_flags_and_duplicate_names_fail(self):
        url = reverse("api:category-list")
        response = self.client.post(url, {"name": "Visible", "is_deleted": True}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertFalse(Category.objects.get(pk=response.data["id"]).is_deleted)
        self.assertEqual(self.client.post(url, {"name": "Visible"}, format="json").status_code, 400)
