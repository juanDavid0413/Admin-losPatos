from django.views.generic import ListView, View, CreateView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from apps.core.mixins import WorkerRequiredMixin, AdminRequiredMixin
from apps.clients.models import Client
from .models import Machine, MachinePayment
from django.urls import reverse_lazy

class MachineListView(WorkerRequiredMixin, ListView):
    model = Machine
    template_name = 'machines/machine_list.html'
    context_object_name = 'machines'

    def get_queryset(self):
        return Machine.objects.prefetch_related('payments').filter(is_active=True).order_by('name')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['recent_payments'] = MachinePayment.objects.select_related(
            'machine', 'worker', 'client'
        ).order_by('-created_at')[:20]
        # Pasar clientes para el select del formulario
        ctx['clients'] = Client.objects.filter(is_active=True).order_by('name')
        return ctx

class MachineCreateView(AdminRequiredMixin, CreateView):
    model = Machine
    fields = ['name', 'description', 'is_active']
    template_name = 'machines/form.html'
    success_url = reverse_lazy('machines:list')

    def form_valid(self, form):
        messages.success(self.request, 'Máquina creada.')
        return super().form_valid(form)


class MachinePaymentView(WorkerRequiredMixin, View):
    def post(self, request, pk):
        machine = get_object_or_404(Machine, pk=pk)

        raw_amount = request.POST.get('amount', '').strip()
        if not raw_amount:
            messages.error(request, 'Ingresa un monto valido.')
            return redirect('machines:list')

        try:
            amount = Decimal(raw_amount).quantize(Decimal('1'))
        except Exception:
            messages.error(request, f'Monto invalido: "{raw_amount}"')
            return redirect('machines:list')

        if amount <= 0:
            messages.error(request, 'El monto debe ser mayor a cero.')
            return redirect('machines:list')

        # Cliente OPCIONAL
        client = None
        client_id = request.POST.get('client', '').strip()
        if client_id:
            try:
                client = Client.objects.get(pk=int(client_id))
            except (Client.DoesNotExist, ValueError, TypeError):
                pass

        notes = request.POST.get('notes', '').strip()

        # Crear pago
        payment = MachinePayment.objects.create(
            machine=machine,
            amount=amount,
            client=client,
            notes=notes,
            worker=request.user,
        )

        # Registrar movimiento — capturar cualquier error
        try:
            from apps.movements.models import Movement
            from apps.core.constants import MovementType, MovementSource
            client_label = f' — {client.name}' if client else ''
            Movement.objects.create(
                movement_type=MovementType.EXPENSE,
                source=MovementSource.MACHINE,
                amount=amount,
                description=f'Pago maquina {machine.name}{client_label}',
                machine_payment=payment,
                client=client,
                worker=request.user,
            )
        except Exception as e:
            messages.warning(request, f'Pago guardado pero error registrando movimiento: {e}')
            return redirect('machines:list')

        label = f' — {client.name}' if client else ''
        messages.success(request, f'Pago de ${amount} en {machine.name}{label} registrado.')
        return redirect('machines:list')
