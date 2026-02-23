from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.tables.models import Table
from apps.table_sessions.models import TableSession
from apps.movements.models import Movement
from django.utils import timezone
from django.db.models import Sum


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # status es @property, no campo DB → calculamos con sesiones activas
        occupied_table_ids = TableSession.objects.filter(
            closed_at__isnull=True
        ).values_list('table_id', flat=True)

        all_tables = Table.objects.filter(is_active=True)
        ctx['tables_occupied'] = all_tables.filter(id__in=occupied_table_ids).count()
        ctx['tables_free'] = all_tables.exclude(id__in=occupied_table_ids).count()
        ctx['active_sessions'] = TableSession.objects.filter(closed_at__isnull=True).count()
        ctx['today_income'] = Movement.objects.filter(
            created_at__date=today,
            movement_type='ingreso'
        ).aggregate(total=Sum('amount'))['total'] or 0

        return ctx
