from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import api_views, auth_views
from .category_views import CategoryViewSet

app_name = "api"

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")

urlpatterns = [
    path("auth/register/", auth_views.RegisterView.as_view(), name="register"),
    path("auth/csrf/", auth_views.CsrfView.as_view(), name="auth-csrf"),
    path("auth/login/", auth_views.CookieLoginView.as_view(), name="auth-login"),
    path("auth/refresh/", auth_views.CookieRefreshView.as_view(), name="auth-refresh"),
    path("auth/logout/", auth_views.CookieLogoutView.as_view(), name="auth-logout"),
    path("token/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("subtasks/", api_views.SubTaskListCreateView.as_view(), name="subtask-list-create"),
    path("subtasks/<uuid:pk>/", api_views.SubTaskDetailUpdateDeleteView.as_view(),
         name="subtask-detail"),
    path("tasks/create/", api_views.TaskCreateView.as_view(), name="task-create"),
    path("tasks/", api_views.TaskListCreateView.as_view(), name="task-list"),
    path("tasks/mine/", api_views.MyTaskListView.as_view(), name="task-mine"),
    path("tasks/statistics/", api_views.task_statistics, name="task-statistics"),
    path("tasks/<uuid:pk>/", api_views.TaskDetailUpdateDeleteView.as_view(), name="task-detail"),
] + router.urls
