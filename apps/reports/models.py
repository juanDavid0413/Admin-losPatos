from django.db import models
from django.conf import settings
from django.utils import timezone


class UserSession(models.Model):
    """Registro de inicio y fin de sesion de cada usuario en el sistema."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_sessions',
        verbose_name='Usuario'
    )
    login_at = models.DateTimeField(default=timezone.now, verbose_name='Inicio de sesion')
    logout_at = models.DateTimeField(null=True, blank=True, verbose_name='Fin de sesion')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP')
    session_key = models.CharField(max_length=40, blank=True, verbose_name='Session key')

    class Meta:
        verbose_name = 'Sesion de Usuario'
        verbose_name_plural = 'Sesiones de Usuario'
        ordering = ['-login_at']

    def __str__(self):
        return f'{self.user} — {self.login_at:%d/%m/%Y %H:%M}'

    @property
    def duration_minutes(self):
        if self.logout_at:
            return int((self.logout_at - self.login_at).total_seconds() / 60)
        return None

    @property
    def is_active(self):
        return self.logout_at is None
