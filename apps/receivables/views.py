from django.views.generic import ListView, View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Sum
from decimal import Decimal, InvalidOperation
from apps.core.mixins import WorkerRequiredMixin
from apps.clients.models import Client
from .models import Receivable, ReceivablePayment


class ReceivableListView(WorkerRequiredMixin, ListView):
    model = Receivable
    template_name = 'receivables/receivable_list.html'
    context_object_name = 'receivables'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        pending_qs = Receivable.objects.filter(
            status=Receivable.STATUS_PENDING
        ).select_related('client', 'table_session__table', 'product_account').order_by('client__name', '-created_at')

        # Agrupar por cliente
        clients_map = {}
        for r in pending_qs:
            cid = r.client_id
            if cid not in clients_map:
                clients_map[cid] = {
                    'client': r.client,
                    'debts': [],
                    'total': Decimal('0'),
                    'total_paid': Decimal('0'),
                }
            clients_map[cid]['debts'].append(r)
            clients_map[cid]['total'] += r.amount
            clients_map[cid]['total_paid'] += r.amount_paid

        # Calcular balance por cliente
        for c in clients_map.values():
            c['balance'] = c['total'] - c['total_paid']

        ctx['clients_debts'] = list(clients_map.values())
        ctx['grand_total_pending'] = sum(c['balance'] for c in clients_map.values())

        ctx['paid_recently'] = Receivable.objects.filter(
            status=Receivable.STATUS_PAID
        ).select_related('client', 'paid_by').order_by('-paid_at')[:20]

        return ctx


class ReceivableApplyPaymentView(WorkerRequiredMixin, View):
    """Registra un abono (parcial o total) a una deuda específica."""

    def post(self, request, pk):
        receivable = get_object_or_404(Receivable, pk=pk, status=Receivable.STATUS_PENDING)
        raw = request.POST.get('amount', '').strip()

        try:
            amount = Decimal(raw.replace(',', '.'))
        except InvalidOperation:
            messages.error(request, 'Monto invalido.')
            return redirect('receivables:list')

        try:
            receivable.apply_payment(amount=amount, worker=request.user)
            # Registrar también en ReceivablePayment para historial
            ReceivablePayment.objects.create(
                receivable=receivable,
                amount=amount,
                worker=request.user,
            )
            if receivable.status == Receivable.STATUS_PAID:
                messages.success(request, f'Deuda de {receivable.client} saldada completamente.')
            else:
                messages.success(request, f'Abono de ${amount} registrado. Saldo pendiente: ${receivable.balance}')
        except ValueError as e:
            messages.error(request, str(e))

        return redirect('receivables:list')
