from django.db.models import Count
from django.db.models.functions import ExtractWeekDay
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from .models import SubTask, Task
from .pagination import SubTaskPagination
from .serializers import (
    SubTaskCreateSerializer, SubTaskSerializer, TaskCreateSerializer,
    TaskDetailSerializer, TaskSerializer,
)


@api_view(["POST"])
def task_create(request):
    serializer = TaskCreateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def task_list(request):
    tasks = Task.objects.all()
    weekday = request.query_params.get("weekday")
    if weekday:
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
        tasks = tasks.annotate(weekday=ExtractWeekDay("deadline")).filter(weekday=number)
    serializer = TaskSerializer(tasks, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def task_detail(request, pk):
    try:
        task = Task.objects.prefetch_related("subtasks").get(pk=pk)
    except Task.DoesNotExist:
        return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response(TaskDetailSerializer(task).data)


@api_view(["GET"])
def task_statistics(request):
    tasks = Task.objects.all()
    total = tasks.aggregate(total=Count("id"))["total"]
    grouped = tasks.order_by().values("status").annotate(count=Count("id"))
    by_status = {value: 0 for value in Task.Status.values}
    by_status.update({row["status"]: row["count"] for row in grouped})
    # Here "overdue" means an expired deadline, regardless of task status.
    overdue = tasks.filter(deadline__lt=timezone.now()).count()
    return Response({"total": total, "by_status": by_status, "overdue": overdue})


class SubTaskListCreateView(APIView):
    def get(self, request):
        subtasks = SubTask.objects.all()
        task_title = request.query_params.get("task_title")
        subtask_status = request.query_params.get("status")
        if task_title:
            subtasks = subtasks.filter(task__title=task_title)
        if subtask_status:
            if subtask_status not in Task.Status.values:
                raise ValidationError({"status": "Invalid subtask status."})
            subtasks = subtasks.filter(status=subtask_status)
        subtasks = subtasks.order_by("-created_at", "-pk")
        paginator = SubTaskPagination()
        page = paginator.paginate_queryset(subtasks, request, view=self)
        return paginator.get_paginated_response(SubTaskSerializer(page, many=True).data)

    def post(self, request):
        serializer = SubTaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SubTaskDetailUpdateDeleteView(APIView):
    def get(self, request, pk):
        subtask = get_object_or_404(SubTask, pk=pk)
        return Response(SubTaskSerializer(subtask).data)

    def put(self, request, pk):
        subtask = get_object_or_404(SubTask, pk=pk)
        serializer = SubTaskCreateSerializer(subtask, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, pk):
        subtask = get_object_or_404(SubTask, pk=pk)
        serializer = SubTaskCreateSerializer(subtask, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        subtask = get_object_or_404(SubTask, pk=pk)
        subtask.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
