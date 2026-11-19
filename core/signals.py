from functools import partial

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Task


@receiver(pre_save, sender=Task)
def remember_task_status(sender, instance, raw, using, update_fields, **kwargs):
    if raw or (update_fields is not None and "status" not in update_fields):
        return

    instance._previous_status = (
        sender.objects.using(using)
        .select_for_update()
        .filter(pk=instance.pk)
        .values_list("status", flat=True)
        .first()
    )


@receiver(post_save, sender=Task)
def notify_task_owner(sender, instance, created, raw, using, update_fields, **kwargs):
    if created or raw or (update_fields is not None and "status" not in update_fields):
        return

    previous_status = instance._previous_status
    if previous_status is None or previous_status == instance.status:
        return

    title, email = sender.objects.using(using).values_list("title", "owner__email").get(pk=instance.pk)
    if not email:
        return

    subject = "Task closed" if instance.status == Task.Status.DONE else "Task status changed"
    message = f'Task "{title}": {Task.Status(previous_status).label} → {instance.get_status_display()}.'
    transaction.on_commit(
        partial(send_mail, subject, message, settings.DEFAULT_FROM_EMAIL, [email]),
        using=using,
        robust=True,
    )
