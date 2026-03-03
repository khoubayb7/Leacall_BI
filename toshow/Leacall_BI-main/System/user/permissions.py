from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.permissions import BasePermission


# ─────────────────────────────────────────
#  DRF Permissions  (for API views)
# ─────────────────────────────────────────

class IsAdminTenancy(BasePermission):
    """Autorise uniquement les utilisateurs avec le rôle 'admin'."""
    message = "Accès réservé aux administrateurs."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'admin'
        )


class IsClientTenancy(BasePermission):
    """Autorise uniquement les utilisateurs avec le rôle 'client'."""
    message = "Accès réservé aux clients."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'client'
        )
