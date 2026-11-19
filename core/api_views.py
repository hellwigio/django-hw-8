from django.db.models import Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.decorators import api_view
from rest_framework.generics import CreateAPIView, ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import SubTaskFilter, TaskFilter
from .models import SubTask, Task
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    SubTaskCreateSerializer, TaskCreateSerializer, TaskDetailSerializer, TaskSerializer,
)


class AssignOwnerOnCreate:
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TaskListCreateView(AssignOwnerOnCreate, ListCreateAPIView):
    queryset = Task.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TaskFilter
    search_fields = ["title", "description"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at", "-pk"]

    def get_serializer_class(self):
        return TaskCreateSerializer if self.request.method == "POST" else TaskSerializer


class TaskCreateView(AssignOwnerOnCreate, CreateAPIView):
    """Keep the earlier /tasks/create/ URL available for existing clients."""
    queryset = Task.objects.all()
    serializer_class = TaskCreateSerializer


class TaskDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    queryset = Task.objects.prefetch_related("subtasks")

    def get_serializer_class(self):
        return TaskDetailSerializer if self.request.method == "GET" else TaskCreateSerializer


class MyTaskListView(ListAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()
        return self.queryset.filter(owner=self.request.user)


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



class SubTaskListCreateView(AssignOwnerOnCreate, ListCreateAPIView):
    queryset = SubTask.objects.all()
    serializer_class = SubTaskCreateSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SubTaskFilter
    search_fields = ["title", "description"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at", "-pk"]


class SubTaskDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    queryset = SubTask.objects.all()
    serializer_class = SubTaskCreateSerializer
