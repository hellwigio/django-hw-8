from django.db.models import Count
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Category
from .serializers import CategoryCreateSerializer


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategoryCreateSerializer
    lookup_value_regex = "[0-9a-fA-F-]{36}"

    @action(detail=False, methods=["get"])
    def count_tasks(self, request):
        categories = self.get_queryset().annotate(task_count=Count("task", distinct=True))
        return Response([
            {"id": str(category.pk), "name": category.name, "task_count": category.task_count}
            for category in categories
        ])
