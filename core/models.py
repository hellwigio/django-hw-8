from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Task(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        IN_PROGRESS = "in_progress", "In progress"
        PENDING = "pending", "Pending"
        BLOCKED = "blocked", "Blocked"
        DONE = "done", "Done"

    title = models.CharField(max_length=255, unique_for_date="deadline")
    description = models.TextField()
    categories = models.ManyToManyField(Category, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class SubTask(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="subtasks")
    status = models.CharField(max_length=20, choices=Task.Status.choices, default=Task.Status.NEW)
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
