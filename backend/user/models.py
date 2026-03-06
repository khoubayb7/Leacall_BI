from django.contrib.auth.models import AbstractUser
from django.db import models


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

    def __str__(self):
        return f"{self.username} ({self.role})"
