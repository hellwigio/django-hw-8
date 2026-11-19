from django.conf import settings
from django.db import models

from .base import TimeStampedModel, UUIDv7Model


class Task(UUIDv7Model, TimeStampedModel):
    class Status(models.TextChoices):
        NEW = "new", "New"
        IN_PROGRESS = "in_progress", "In progress"
        PENDING = "pending", "Pending"
        BLOCKED = "blocked", "Blocked"
        DONE = "done", "Done"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="owned_tasks",
    )
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    categories = models.ManyToManyField("Category", blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    deadline = models.DateTimeField()

    class Meta:
        db_table = "task_manager_task"
        ordering = ["-created_at"]
        verbose_name = "Task"
        verbose_name_plural = "Tasks"

    def __str__(self):
        return self.title
