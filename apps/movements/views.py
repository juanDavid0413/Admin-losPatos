from django.views.generic import ListView, DetailView
from django.db.models import Sum
from apps.core.mixins import WorkerRequiredMixin
from apps.users.models import User
from apps.clients.models import Client
from .models import Movement


class MovementListView(WorkerRequiredMixin, ListView):
    model = Movement
    template_name = 'movements/movement_list.html'
    context_object_name = 'movements'
    paginate_by = 100

    def get_queryset(self):
        qs = Movement.objects.select_related(
            'worker', 'client', 'table_session__table',
            'product_account', 'machine_payment'
        ).order_by('-created_at')

        worker = self.request.GET.get('worker')
        source = self.request.GET.get('source')
        client = self.request.GET.get('client')
        q = self.request.GET.get('q')

        if worker:
            qs = qs.filter(worker_id=worker)
        if source:
            qs = qs.filter(source=source)
        if client:
            qs = qs.filter(client_id=client)
        if q:
            qs = qs.filter(description__icontains=q)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        ctx['workers'] = User.objects.filter(is_active=True)
        ctx['clients'] = Client.objects.filter(is_active=True)
        ctx['total_income'] = qs.filter(movement_type='ingreso').aggregate(
            t=Sum('amount'))['t'] or 0
        ctx['total_expense'] = qs.filter(movement_type='egreso').aggregate(
            t=Sum('amount'))['t'] or 0
        return ctx


class MovementDetailView(WorkerRequiredMixin, DetailView):
    model = Movement
    template_name = 'movements/movement_detail.html'
    context_object_name = 'movement'