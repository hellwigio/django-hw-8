from django.db.models.functions import ExtractWeekDay
from django_filters import rest_framework as filters
from rest_framework.exceptions import ValidationError

from .models import SubTask, Task


class TaskFilter(filters.FilterSet):
    weekday = filters.CharFilter(method="filter_weekday")

    class Meta:
        model = Task
        fields = ["status", "deadline"]

    def filter_weekday(self, queryset, name, weekday):
        # ExtractWeekDay uses Sunday=1, Monday=2, ..., Saturday=7.
        names = {
            "sunday": 1, "monday": 2, "tuesday": 3, "wednesday": 4,
            "thursday": 5, "friday": 6, "saturday": 7,
            "воскресенье": 1, "понедельник": 2, "вторник": 3, "среда": 4,
            "четверг": 5, "пятница": 6, "суббота": 7,
        }
        value = weekday.strip().lower()
        number = int(value) if value in {"1", "2", "3", "4", "5", "6", "7"} else names.get(value)
        if number is None:
            raise ValidationError({"weekday": "Use 1-7 (Sunday=1), or a weekday name."})
        queryset = queryset.annotate(weekday=ExtractWeekDay("deadline")).filter(weekday=number)
        return queryset


class SubTaskFilter(filters.FilterSet):
    task_title = filters.CharFilter(field_name="task__title")

    class Meta:
        model = SubTask
        fields = ["status", "deadline", "task_title"]
