from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from core.models import SubTask, Task


class Homework10Tests(TestCase):
    def test_crud_cascades_and_preserves_existing_records(self):
        existing = Task.objects.create(
            title="Existing task",
            description="Keep this task",
            deadline=timezone.now() + timedelta(days=1),
        )
        subtask = SubTask.objects.create(
            task=existing,
            title="Already done",
            description="Existing overdue subtask",
            status=Task.Status.DONE,
            deadline=timezone.now() - timedelta(days=1),
        )
        for _ in range(2):
            output = StringIO()
            call_command("homework10", stdout=output)
            self.assertEqual(list(Task.objects.values_list("pk", flat=True)), [existing.pk])
            self.assertEqual(list(SubTask.objects.values_list("pk", flat=True)), [subtask.pk])
            self.assertIn("Already done", output.getvalue())
            self.assertIn("Task exists: False", output.getvalue())
            self.assertIn("Remaining subtasks: 0", output.getvalue())
            self.assertIn("Create and format presentation slides", output.getvalue())
