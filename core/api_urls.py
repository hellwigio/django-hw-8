from django.urls import path

from . import api_views

app_name = "api"

urlpatterns = [
    path("subtasks/", api_views.SubTaskListCreateView.as_view(), name="subtask-list-create"),
    path("subtasks/<uuid:pk>/", api_views.SubTaskDetailUpdateDeleteView.as_view(),
         name="subtask-detail"),
    path("tasks/create/", api_views.task_create, name="task-create"),
    path("tasks/", api_views.task_list, name="task-list"),
    path("tasks/statistics/", api_views.task_statistics, name="task-statistics"),
    path("tasks/<uuid:pk>/", api_views.task_detail, name="task-detail"),
]
