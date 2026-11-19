from django.contrib.auth import get_user_model
from django.core import mail
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from core.api_test_helpers import AuthenticatedAPITestCase
from core.models import Task


class TaskStatusEmailTests(AuthenticatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.owner = get_user_model().objects.get(username="api-test")
        self.owner.email = "owner@example.com"
        self.owner.save(update_fields=["email"])

    def test_api_notifies_owner_on_actual_transitions_only(self):
        with self.captureOnCommitCallbacks(execute=True):
            task = Task.objects.create(title="Demo", owner=self.owner, deadline=timezone.now())
            url = reverse("api:task-detail", args=[task.pk])
            for status in ("in_progress", "in_progress", "done", "done"):
                self.assertEqual(self.client.patch(url, {"status": status}).status_code, 200)
        self.assertEqual([message.subject for message in mail.outbox], ["Task status changed", "Task closed"])
        self.assertTrue(all(message.to == ["owner@example.com"] for message in mail.outbox))
        self.assertIn("New → In progress", mail.outbox[0].body)
        self.assertIn("In progress → Done", mail.outbox[1].body)

    def test_rollback_and_save_without_status_do_not_send(self):
        task = Task.objects.create(title="Demo", owner=self.owner, deadline=timezone.now())
        with self.captureOnCommitCallbacks(execute=True):
            task.status = Task.Status.DONE
            task.save(update_fields=["title"])
            with transaction.atomic():
                task.save(update_fields=["status"])
                transaction.set_rollback(True)
        self.assertEqual(mail.outbox, [])
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.NEW)
