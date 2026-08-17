from django.urls import path

from .views import (
    DocumentDetailView,
    DocumentListCreateView,
    DocumentPresignedUrlView,
    DocumentReprocessView,
)

urlpatterns = [
    path("", DocumentListCreateView.as_view(), name="document_list_create"),
    path("<int:pk>/", DocumentDetailView.as_view(), name="document_detail"),
    path(
        "<int:pk>/reprocess/",
        DocumentReprocessView.as_view(),
        name="document_reprocess",
    ),
    path("<int:pk>/url/", DocumentPresignedUrlView.as_view(), name="document_url"),
]
