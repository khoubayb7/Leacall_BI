from django.contrib.auth.models import AbstractUser
from django.db import models


def default_client_modules():
    return ["dashboard"]


class CustomUser(AbstractUser):

    class Role(models.TextChoices):
        ADMIN  = 'admin',  'Admin'
        CLIENT = 'client', 'Client'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CLIENT,
    )

    # Rempli par l'admin lors de la création du compte client
    leacall_tenancy_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL de la tenancy leacall du client."
    )

    leacall_api_key = models.CharField(
        max_length=512,
        blank=True,
        default="",
        help_text="Clé API pour s'authentifier auprès du serveur LeaCall.",
    )

    # List of enabled modules in the client UI.
    enabled_modules = models.JSONField(
        default=default_client_modules,
        blank=True,
        help_text="Enabled modules for the client workspace."
    )

    def __str__(self):
        return f"{self.username} ({self.role})"
