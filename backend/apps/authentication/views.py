from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import RegisterSerializer, UserSerializer
from .models import QuotaChangeLog

User = get_user_model()

class IsAdminUser(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == 'ADMIN'


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


class CurrentUserView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

class AdminUserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser,)

class AdminUserQuotaUpdateView(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            
        max_docs = request.data.get('max_documents')
        max_storage = request.data.get('max_storage_bytes')
        
        if max_docs is not None:
            user.max_documents = max_docs
        if max_storage is not None:
            user.max_storage_bytes = max_storage
            
        user.save()
        
        # Log the change
        QuotaChangeLog.objects.create(
            user=user,
            changed_by=request.user,
            new_max_documents=user.max_documents,
            new_max_storage_bytes=user.max_storage_bytes,
            reason=request.data.get('reason', '')
        )
        return Response({"status": "Quotas updated"})

class AdminNotifyView(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request):
        subject = request.data.get('subject')
        message = request.data.get('message')
        user_ids = request.data.get('user_ids') # list of ids or 'all'
        
        if not subject or not message:
            return Response({"error": "Subject and message required"}, status=status.HTTP_400_BAD_REQUEST)
            
        if user_ids == 'all':
            users = User.objects.all()
        else:
            users = User.objects.filter(id__in=user_ids)
            
        recipient_list = [u.email for u in users if u.email]
        
        if recipient_list:
            from .tasks import send_email_notification_task
            send_email_notification_task.delay(subject, message, recipient_list)
            
        return Response({"status": f"Notifications sent to {len(recipient_list)} users."})
