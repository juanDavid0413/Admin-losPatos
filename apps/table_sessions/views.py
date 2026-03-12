from django.views.generic import ListView, CreateView, DetailView, View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from apps.core.mixins import WorkerRequiredMixin
from apps.products.models import Product
from .models import TableSession, SessionProduct
from .forms import TableSessionForm, SessionProductForm


class SessionListView(WorkerRequiredMixin, ListView):
    model = TableSession
    template_name = 'table_sessions/session_list.html'
    context_object_name = 'sessions'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['open_sessions'] = TableSession.objects.select_related(
            'table', 'client', 'worker'
        ).filter(closed_at__isnull=True).order_by('-opened_at')
        ctx['closed_sessions'] = TableSession.objects.select_related(
            'table', 'client', 'worker'
        ).filter(closed_at__isnull=False).order_by('-closed_at')[:30]
        return ctx


class SessionOpenView(WorkerRequiredMixin, CreateView):
    model = TableSession
    form_class = TableSessionForm
    template_name = 'table_sessions/session_open.html'

    def form_valid(self, form):
        session = form.save(commit=False)
        if not session.table.is_free:
            messages.error(self.request, f'La mesa {session.table.name} ya tiene una sesion activa.')
            return self.form_invalid(form)
        session.worker = self.request.user

        # Si es cliente de paso, guardar alias en notas
        alias = self.request.POST.get('walkup_alias', '').strip()
        if alias and 'de paso' in session.client.name.lower():
            session.notes = f'[Alias: {alias}]'

        session.save()
        label = f'"{alias}"' if alias else session.client.name
        messages.success(self.request, f'Sesion abierta en {session.table.name} para {label}.')
        return redirect('table_sessions:detail', pk=session.pk)


class SessionDetailView(WorkerRequiredMixin, DetailView):
    model = TableSession
    template_name = 'table_sessions/session_detail.html'
    context_object_name = 'session'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['product_form'] = SessionProductForm()
        ctx['products'] = self.object.session_products.select_related('product').all()
        ctx['products_cost'] = self.object.calculate_products_cost()

        # Extraer alias si es cliente de paso
        alias = ''
        if self.object.notes and self.object.notes.startswith('[Alias:'):
            alias = self.object.notes.replace('[Alias:', '').replace(']', '').strip()
        ctx['walkup_alias'] = alias
        return ctx


class SessionAddProductView(WorkerRequiredMixin, View):
    def post(self, request, pk):
        session = get_object_or_404(TableSession, pk=pk, closed_at__isnull=True)
        form = SessionProductForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            quantity = form.cleaned_data['quantity']
            try:
                SessionProduct.objects.create(
                    session=session, product=product,
                    quantity=quantity, unit_price=product.sale_price
                )
                messages.success(request, f'{product.name} agregado.')
            except ValueError as e:
                messages.error(request, str(e))
        return redirect('table_sessions:detail', pk=pk)


class SessionRemoveProductView(WorkerRequiredMixin, View):
    def post(self, request, pk, item_pk):
        session = get_object_or_404(TableSession, pk=pk, closed_at__isnull=True)
        item = get_object_or_404(SessionProduct, pk=item_pk, session=session)
        name = item.product.name
        item.delete()
        messages.success(request, f'{name} eliminado.')
        return redirect('table_sessions:detail', pk=pk)


class SessionPauseView(WorkerRequiredMixin, View):
    def post(self, request, pk):
        session = get_object_or_404(TableSession, pk=pk, closed_at__isnull=True)
        try:
            session.pause_timer()
            messages.info(request, 'Cronometro pausado.')
        except ValueError as e:
            messages.error(request, str(e))
        return redirect('table_sessions:detail', pk=pk)


class SessionResumeView(WorkerRequiredMixin, View):
    def post(self, request, pk):
        session = get_object_or_404(TableSession, pk=pk, closed_at__isnull=True)
        try:
            session.resume_timer()
            messages.success(request, 'Cronometro reanudado.')
        except ValueError as e:
            messages.error(request, str(e))
        return redirect('table_sessions:detail', pk=pk)


class SessionStopTimerView(WorkerRequiredMixin, View):
    def post(self, request, pk):
        session = get_object_or_404(TableSession, pk=pk, closed_at__isnull=True)
        try:
            session.stop_timer()
            messages.warning(request, 'Tiempo detenido. Puedes seguir agregando productos.')
        except ValueError as e:
            messages.error(request, str(e))
        return redirect('table_sessions:detail', pk=pk)


class SessionCloseView(WorkerRequiredMixin, View):
    def post(self, request, pk):
        session = get_object_or_404(TableSession, pk=pk, closed_at__isnull=True)
        paid = request.POST.get('paid', '1') == '1'
        try:
            session.close(worker=request.user, paid=paid)
            if paid:
                messages.success(request, f'Sesion cerrada y cobrada. Total: ${session.grand_total}')
            else:
                messages.warning(request, f'Sesion cerrada. ${session.grand_total} quedaron como cuenta por cobrar.')
        except ValueError as e:
            messages.error(request, str(e))
        return redirect('table_sessions:list')
