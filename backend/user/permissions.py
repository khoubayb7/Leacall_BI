from rest_framework.permissions import BasePermission

class RolePermission(BasePermission):
    allowed_role = None

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == self.allowed_role
        )
        
        
class IsAdmin(RolePermission):
    allowed_role = "admin"
    message = "Accès réservé aux administrateurs."


class IsClient(RolePermission):
    allowed_role = "client"
    message = "Accès réservé aux clients."
