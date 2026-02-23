"""
Mixins reutilizables para views y modelos.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Solo admins pueden acceder a esta vista."""

    def test_func(self):
        return self.request.user.is_admin()

    def handle_no_permission(self):
        messages.error(self.request, 'No tienes permisos para acceder a esta sección.')
        return redirect('core:dashboard')


class WorkerRequiredMixin(LoginRequiredMixin):
    """Cualquier usuario autenticado (admin o trabajador)."""
    pass


class TimestampMixin(object):
    """
    Mixin para modelos que necesitan created_at / updated_at.
    Se usa junto con models.Model.
    """
    # Los campos se declaran en el modelo que lo use,
    # aquí solo se agrupan métodos de utilidad.

    def get_created_display(self):
        return self.created_at.strftime('%d/%m/%Y %H:%M')

    def get_updated_display(self):
        return self.updated_at.strftime('%d/%m/%Y %H:%M')
