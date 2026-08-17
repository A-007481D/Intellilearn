from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    CurrentUserView,
    RegisterView,
    AdminUserListView,
    AdminUserQuotaUpdateView,
    AdminNotifyView
)

urlpatterns = [
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("login/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("register/", RegisterView.as_view(), name="auth_register"),
    path("me/", CurrentUserView.as_view(), name="auth_me"),
    path("admin/users/", AdminUserListView.as_view(), name="admin_user_list"),
    path("admin/users/<int:pk>/quotas/", AdminUserQuotaUpdateView.as_view(), name="admin_user_quotas"),
    path("admin/notify/", AdminNotifyView.as_view(), name="admin_notify"),
]
