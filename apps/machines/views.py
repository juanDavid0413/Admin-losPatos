from django.views.generic import ListView, CreateView
from django.contrib import messages
from django.urls import reverse_lazy
from apps.core.mixins import WorkerRequiredMixin, AdminRequiredMixin
from .models import Machine, MachinePayment


class MachineListView(WorkerRequiredMixin, ListView):
    model = Machine
    template_name = 'machines/machine_list.html'
    context_object_name = 'machines'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['recent_payments'] = MachinePayment.objects.select_related('machine', 'client', 'worker').order_by('-created_at')[:10]
        return ctx


class MachineCreateView(AdminRequiredMixin, CreateView):
    model = Machine
    fields = ['name', 'description', 'is_active']
    template_name = 'machines/form.html'
    success_url = reverse_lazy('machines:list')

    def form_valid(self, form):
        messages.success(self.request, 'Máquina creada.')
        return super().form_valid(form)


class MachinePaymentCreateView(WorkerRequiredMixin, CreateView):
    model = MachinePayment
    fields = ['machine', 'client', 'amount', 'notes']
    template_name = 'machines/payment_form.html'
    success_url = reverse_lazy('machines:list')

    def form_valid(self, form):
        form.instance.worker = self.request.user
        messages.success(self.request, 'Pago registrado correctamente.')
        return super().form_valid(form)
