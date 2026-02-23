from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.constants import UserRole


class User(AbstractUser):
    """
    Usuario personalizado. Regla del documento: NO usar User por defecto.
    Extendemos AbstractUser para tener flexibilidad total.
    """
    role = models.CharField(
        max_length=20,
        choices=UserRole.CHOICES,
        default=UserRole.WORKER,
        verbose_name='Rol'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    def is_admin(self):
        return self.role == UserRole.ADMIN or self.is_superuser

    def is_worker(self):
        return self.role == UserRole.WORKER
