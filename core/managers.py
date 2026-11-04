from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        count = self.filter(is_deleted=False).update(is_deleted=True, deleted_at=timezone.now())
        return count, {self.model._meta.label: count}


class SoftDeleteManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
