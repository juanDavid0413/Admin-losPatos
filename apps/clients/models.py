from django.db import models


class Client(models.Model):
    """
    Clientes del billar.
    Regla del documento: No dependen de sesiones.
    """
    name = models.CharField(max_length=100, verbose_name='Nombre')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    email = models.EmailField(blank=True, verbose_name='Email')
    notes = models.TextField(blank=True, verbose_name='Notas')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['name']

    def __str__(self):
        return self.name
