from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SubTask, Task
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
    serializer = TaskSerializer(Task.objects.all(), many=True)
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
        return Response(SubTaskSerializer(SubTask.objects.all(), many=True).data)

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
