from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import SubTask, Task


class Homework11AdminTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create_superuser(
            username="admin_test", password="test-only-password"
        ))
        self.task = Task.objects.create(
            title="Prepare presentation", description="Materials",
            deadline=timezone.now() + timedelta(days=3),
        )

    def test_titles_are_short_only_in_task_list(self):
        response = self.client.get(reverse("admin:core_task_changelist"))
        self.assertContains(response, ">Prepare pr...</a>", html=False)
        response = self.client.get(reverse("admin:core_subtask_add"))
        self.assertContains(response, "Prepare presentation</option>", html=False)
        self.assertEqual(str(self.task), "Prepare presentation")

    def test_task_and_inline_subtask_can_be_created_together(self):
        response = self.client.post(reverse("admin:core_task_add"), {
            "title": "Inline task", "description": "Parent", "status": "new",
            "deadline_0": "2026-12-10", "deadline_1": "12:00:00",
            "subtasks-TOTAL_FORMS": "1", "subtasks-INITIAL_FORMS": "0",
            "subtasks-MIN_NUM_FORMS": "0", "subtasks-MAX_NUM_FORMS": "1000",
            "subtasks-0-title": "Inline child", "subtasks-0-description": "Child",
            "subtasks-0-status": "new", "subtasks-0-deadline_0": "2026-12-09",
            "subtasks-0-deadline_1": "12:00:00", "_save": "Save",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SubTask.objects.get(title="Inline child").task.title, "Inline task")

    def test_action_updates_only_selected_subtasks(self):
        children = [SubTask.objects.create(
            task=self.task, title=f"Child {i}", description="Child",
            deadline=self.task.deadline,
        ) for i in range(3)]
        response = self.client.post(reverse("admin:core_subtask_changelist"), {
            "action": "mark_done", "_selected_action": [str(c.pk) for c in children[:2]],
            "index": "0",
        })
        self.assertEqual(response.status_code, 302)
        for child in children[:2]:
            child.refresh_from_db()
            self.assertEqual(child.status, Task.Status.DONE)
        children[2].refresh_from_db()
        self.assertEqual(children[2].status, Task.Status.NEW)

    def test_short_titles_are_not_truncated(self):
        from django.contrib import admin
        model_admin = admin.site._registry[Task]
        for title in ("Short", "1234567890", "12345678901"):
            self.task.title = title
            expected = title if len(title) <= 10 else "1234567890..."
            self.assertEqual(model_admin.short_title(self.task), expected)
