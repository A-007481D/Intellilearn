from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import NotificationLog, QuotaChangeLog
from .serializers import RegisterSerializer, UserSerializer

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
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser,)

    def get_queryset(self):
        qs = User.objects.all().order_by('id')
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(Q(email__icontains=search) | Q(first_name__icontains=search))
        return qs


class AdminUserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser,)


class AdminUserQuotaUpdateView(APIView):
    permission_classes = (IsAdminUser,)

    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Capture old values before change
        old_max_docs = user.max_documents
        old_max_storage = user.max_storage_bytes

        max_docs = request.data.get('max_documents')
        max_storage = request.data.get('max_storage_bytes')
        new_role = request.data.get('role')

        update_fields = []
        if max_docs is not None:
            user.max_documents = int(max_docs)
            update_fields.append('max_documents')
        if max_storage is not None:
            user.max_storage_bytes = int(max_storage)
            update_fields.append('max_storage_bytes')
        if new_role in ('LEARNER', 'ADMIN'):
            user.role = new_role
            update_fields.append('role')

        if update_fields:
            user.save(update_fields=update_fields)

        # Log the change
        QuotaChangeLog.objects.create(
            admin_user=request.user,
            target_user=user,
            old_max_documents=old_max_docs,
            new_max_documents=user.max_documents,
            old_max_storage_bytes=old_max_storage,
            new_max_storage_bytes=user.max_storage_bytes,
            reason=request.data.get('reason', ''),
        )

        return Response(UserSerializer(user).data)


class AdminNotifyView(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request):
        subject = request.data.get('subject')
        message = request.data.get('message')
        user_ids = request.data.get('user_ids')  # list of ids or string 'all'

        if not subject or not message:
            return Response(
                {'error': 'subject and message are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user_ids == 'all':
            users = User.objects.all()
        elif isinstance(user_ids, list):
            users = User.objects.filter(id__in=user_ids)
        else:
            return Response(
                {'error': 'user_ids must be a list of IDs or the string "all"'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logs = []
        recipient_emails = []
        for u in users:
            log = NotificationLog.objects.create(
                sender=request.user,
                recipient=u,
                subject=subject,
                message=message,
                status=NotificationLog.Status.PENDING,
            )
            logs.append(log)
            if u.email:
                recipient_emails.append((u.email, log.id))

        # Dispatch emails via celery
        from .tasks import send_bulk_notification_task
        for email, log_id in recipient_emails:
            send_bulk_notification_task.delay(subject, message, email, log_id)

        return Response({'status': f'Queued {len(logs)} notifications.'})


class NotificationLogListView(generics.ListAPIView):
    permission_classes = (IsAdminUser,)

    def get_queryset(self):
        from .models import NotificationLog
        return NotificationLog.objects.all().order_by('-sent_at')[:100]

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        data = [
            {
                'id': n.id,
                'recipient': n.recipient.email,
                'subject': n.subject,
                'status': n.status,
                'sent_at': n.sent_at,
                'error_message': n.error_message,
            }
            for n in qs
        ]
        return Response(data)
