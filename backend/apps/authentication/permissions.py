from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object or admins to access it.
    Assumes the model instance has an `user` attribute.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if getattr(request.user, "role", "") == "ADMIN":
            return True

        if hasattr(obj, "user"):
            return obj.user == request.user
        elif hasattr(obj, "email"):  # if the object is the User model itself
            return obj == request.user

        return False
