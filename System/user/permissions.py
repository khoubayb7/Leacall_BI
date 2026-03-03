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


# ─────────────────────────────────────────
#  Django Class-Based View Mixins  (for HTML views)
# ─────────────────────────────────────────

class AdminTenancyRequiredMixin(LoginRequiredMixin):
    """Mixin pour les vues réservées à la tenancy admin."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role != 'admin':
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Accès refusé — rôle admin requis.")
        return super().dispatch(request, *args, **kwargs)


class ClientTenancyRequiredMixin(LoginRequiredMixin):
    """Mixin pour les vues réservées à la tenancy client."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role != 'client':
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Accès refusé — rôle client requis.")
        return super().dispatch(request, *args, **kwargs)
