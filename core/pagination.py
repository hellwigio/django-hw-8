from rest_framework.pagination import CursorPagination


class ProjectCursorPagination(CursorPagination):
    ordering = "-pk"
