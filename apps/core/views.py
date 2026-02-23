from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.tables.models import Table
from apps.table_sessions.models import TableSession
from apps.movements.models import Movement
from apps.receivables.models import Receivable
from apps.machines.models import MachinePayment
from apps.core.constants import MovementSource
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # Mesas
        occupied_ids = TableSession.objects.filter(
            closed_at__isnull=True
        ).values_list('table_id', flat=True)
        all_tables = Table.objects.filter(is_active=True)
        ctx['tables_occupied'] = all_tables.filter(id__in=occupied_ids).count()
        ctx['tables_free'] = all_tables.exclude(id__in=occupied_ids).count()
        ctx['active_sessions'] = TableSession.objects.filter(closed_at__isnull=True).count()

        # Ingresos del dia: solo sesiones + cuentas (excluyendo maquinas)
        income_sources = [MovementSource.TABLE_SESSION, MovementSource.PRODUCT_ACCOUNT]
        ctx['today_income'] = Movement.objects.filter(
            created_at__date=today,
            movement_type='ingreso',
            source__in=income_sources,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Pagos a maquinas del dia (egresos del negocio)
        ctx['today_machine_payments'] = MachinePayment.objects.filter(
            created_at__date=today
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Deudas pendientes
        pending = Receivable.objects.filter(status=Receivable.STATUS_PENDING)
        ctx['pending_receivables_count'] = pending.count()
        ctx['pending_receivables_total'] = sum(r.balance for r in pending)

        # Movimientos recientes del dia
        ctx['recent_movements'] = Movement.objects.filter(
            created_at__date=today
        ).select_related('worker').order_by('-created_at')[:8]

        return ctx
