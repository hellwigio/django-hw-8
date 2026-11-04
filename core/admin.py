from django.contrib import admin

from .models import Category, SubTask, Task


class SubTaskInline(admin.StackedInline):
    model = SubTask
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("short_title", "status", "deadline", "created_at")
    list_filter = ("status", "categories")
    search_fields = ("title",)
    inlines = [SubTaskInline]

    @admin.display(description="Title", ordering="title")
    def short_title(self, obj):
        return obj.title[:10] + "..." if len(obj.title) > 10 else obj.title


@admin.register(SubTask)
class SubTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "task", "status", "deadline", "created_at")
    list_filter = ("status",)
    search_fields = ("title",)
    actions = ["mark_done"]

    def mark_done(self, request, queryset):
        queryset.update(status=Task.Status.DONE)

    mark_done.short_description = "Mark selected subtasks as Done"
