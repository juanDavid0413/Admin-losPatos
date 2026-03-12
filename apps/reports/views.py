from django.views.generic import TemplateView
from django.utils import timezone
from django.db.models import Sum, Q
from datetime import timedelta
from apps.core.mixins import WorkerRequiredMixin
from apps.movements.models import Movement
from apps.machines.models import MachinePayment
from apps.core.constants import MovementSource
from .models import UserSession


def get_date_range(period, ref_date=None):
    today = ref_date or timezone.now().date()
    if period == 'day':
        return today, today
    elif period == 'week':
        start = today - timedelta(days=today.weekday())
        return start, start + timedelta(days=6)
    elif period == 'month':
        start = today.replace(day=1)
        if start.month == 12:
            end = start.replace(month=12, day=31)
        else:
            end = start.replace(month=start.month + 1, day=1) - timedelta(days=1)
        return start, end
    return today, today


class ReportView(WorkerRequiredMixin, TemplateView):
    template_name = 'reports/report.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        period = self.request.GET.get('period', 'day')
        ctx['period'] = period

        start, end = get_date_range(period)
        ctx['date_start'] = start
        ctx['date_end'] = end

        income_sources = [MovementSource.TABLE_SESSION, MovementSource.PRODUCT_ACCOUNT]

        movements = Movement.objects.filter(
            created_at__date__gte=start,
            created_at__date__lte=end,
        ).select_related('worker', 'client').order_by('-created_at')

        ctx['movements'] = movements

        # Ingresos directos (cobro inmediato al cerrar)
        direct_income = movements.filter(
            movement_type='ingreso',
            source__in=income_sources,
        ).exclude(
            Q(description__icontains='abono') | Q(description__icontains='cobro deuda') | Q(description__icontains='pago total')
        ).aggregate(t=Sum('amount'))['t'] or 0

        # Todo lo cobrado de deudas (abonos parciales + pagos totales)
        debt_collected = movements.filter(
            movement_type='ingreso',
            source__in=income_sources,
        ).filter(
            Q(description__icontains='abono deuda') |
            Q(description__icontains='cobro deuda') |
            Q(description__icontains='pago total')
        ).aggregate(t=Sum('amount'))['t'] or 0

        ctx['total_income'] = direct_income + debt_collected
        ctx['total_direct_income'] = direct_income
        ctx['total_debt_collected'] = debt_collected

        # Pagos a maquinas
        ctx['total_machines'] = MachinePayment.objects.filter(
            created_at__date__gte=start,
            created_at__date__lte=end,
        ).aggregate(t=Sum('amount'))['t'] or 0

        # Resumen diario
        if period in ('week', 'month'):
            daily = []
            current = start
            while current <= end:
                day_movs = movements.filter(created_at__date=current)
                day_income = day_movs.filter(
                    movement_type='ingreso', source__in=income_sources
                ).aggregate(t=Sum('amount'))['t'] or 0
                day_machines = MachinePayment.objects.filter(
                    created_at__date=current
                ).aggregate(t=Sum('amount'))['t'] or 0
                daily.append({
                    'date': current,
                    'income': day_income,
                    'machines': day_machines,
                    'count': day_movs.count(),
                })
                current += timedelta(days=1)
            ctx['daily_summary'] = daily

        # Sesiones de usuario
        user_sessions = UserSession.objects.filter(
            login_at__date__gte=start,
            login_at__date__lte=end,
        ).select_related('user').order_by('-login_at')

        users_map = {}
        for s in user_sessions:
            uid = s.user_id
            if uid not in users_map:
                users_map[uid] = {
                    'user': s.user,
                    'sessions': [],
                    'total_minutes': 0,
                    'session_count': 0,
                }
            users_map[uid]['sessions'].append(s)
            users_map[uid]['session_count'] += 1
            if s.duration_minutes:
                users_map[uid]['total_minutes'] += s.duration_minutes

        ctx['users_activity'] = list(users_map.values())
        return ctx
