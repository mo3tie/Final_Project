from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """Django staff / administrator accounts only."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )
