from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.models import SubTask, Task


def show(queryset, write=print):
    rows = list(queryset.values("title", "description", "status", "deadline"))
    if not rows:
        write("[] (no matching records)")
    for row in rows:
        write(str(row))


@transaction.atomic
def run(write=print):
    now = timezone.now()

    # Values use the existing model choices; their labels are New / In progress / Done.
    task = Task.objects.create(
        title="Prepare presentation",
        description="Prepare materials and slides for the presentation",
        status=Task.Status.NEW,
        deadline=now + timedelta(days=3),
    )
    gather = SubTask.objects.create(
        task=task,
        title="Gather information",
        description="Find necessary information for the presentation",
        status=Task.Status.NEW,
        deadline=now + timedelta(days=2),
    )
    slides = SubTask.objects.create(
        task=task,
        title="Create slides",
        description="Create presentation slides",
        status=Task.Status.NEW,
        deadline=now + timedelta(days=1),
    )
    write("1. CREATE")
    show(Task.objects.filter(pk=task.pk), write)
    show(task.subtasks.all(), write)

    write("\n2. READ: tasks with status New")
    show(Task.objects.filter(status=Task.Status.NEW), write)
    write("READ: overdue subtasks with status Done")
    show(SubTask.objects.filter(status=Task.Status.DONE, deadline__lt=now), write)

    Task.objects.filter(pk=task.pk).update(status=Task.Status.IN_PROGRESS)
    SubTask.objects.filter(pk=gather.pk).update(deadline=now - timedelta(days=2))
    SubTask.objects.filter(pk=slides.pk).update(
        description="Create and format presentation slides"
    )
    write("\n3. UPDATE")
    show(Task.objects.filter(pk=task.pk), write)
    show(task.subtasks.all(), write)

    task_id = task.pk
    deleted, breakdown = task.delete()
    write(f"\n4. DELETE: {deleted} objects; {breakdown}")
    write(f"Task exists: {Task.objects.filter(pk=task_id).exists()}")
    write(f"Remaining subtasks: {SubTask.objects.filter(task_id=task_id).count()}")
