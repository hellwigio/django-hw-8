from django.db import models
from django.utils import timezone

from core.managers import SoftDeleteManager
from .base import UUIDv7Model


class Category(UUIDv7Model):
    name = models.CharField(max_length=100, unique=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def delete(self, using=None, keep_parents=False):
        if self.is_deleted:
            return 0, {self._meta.label: 0}
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(using=using, update_fields=["is_deleted", "deleted_at"])
        return 1, {self._meta.label: 1}

    class Meta:
        db_table = "task_manager_category"
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name
