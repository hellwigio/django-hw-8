from django.db.models import Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.decorators import api_view
from rest_framework.generics import CreateAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response

from .filters import SubTaskFilter, TaskFilter
from .models import SubTask, Task
from .serializers import (
    SubTaskCreateSerializer, TaskCreateSerializer, TaskDetailSerializer, TaskSerializer,
)


class TaskListCreateView(ListCreateAPIView):
    queryset = Task.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TaskFilter
    search_fields = ["title", "description"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at", "-pk"]

    def get_serializer_class(self):
        return TaskCreateSerializer if self.request.method == "POST" else TaskSerializer


class TaskCreateView(CreateAPIView):
    """Keep the earlier /tasks/create/ URL available for existing clients."""
    queryset = Task.objects.all()
    serializer_class = TaskCreateSerializer


class TaskDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.prefetch_related("subtasks")

    def get_serializer_class(self):
        return TaskDetailSerializer if self.request.method == "GET" else TaskCreateSerializer


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



class SubTaskListCreateView(ListCreateAPIView):
    queryset = SubTask.objects.all()
    serializer_class = SubTaskCreateSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SubTaskFilter
    search_fields = ["title", "description"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at", "-pk"]


class SubTaskDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    queryset = SubTask.objects.all()
    serializer_class = SubTaskCreateSerializer
