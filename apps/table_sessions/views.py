from django.views.generic import ListView, CreateView, DetailView, View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from apps.core.mixins import WorkerRequiredMixin
from apps.products.models import Product
from .models import TableSession, SessionProduct
from .forms import TableSessionForm, SessionProductForm


class SessionListView(WorkerRequiredMixin, ListView):
    model = TableSession
    template_name = "table_sessions/session_list.html"
    context_object_name = "sessions"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["open_sessions"] = TableSession.objects.select_related(
            "table", "client", "worker"
        ).filter(closed_at__isnull=True).order_by("-opened_at")
        ctx["closed_sessions"] = TableSession.objects.select_related(
            "table", "client", "worker"
        ).filter(closed_at__isnull=False).order_by("-closed_at")[:30]
        return ctx


class SessionOpenView(WorkerRequiredMixin, CreateView):
    model = TableSession
    form_class = TableSessionForm
    template_name = "table_sessions/session_open.html"

    def form_valid(self, form):
        session = form.save(commit=False)
        if not session.table.is_free:
            messages.error(self.request, f"La mesa {session.table.name} ya tiene una sesión activa.")
            return self.form_invalid(form)
        session.worker = self.request.user
        session.save()
        messages.success(self.request, f"Sesión abierta en {session.table.name}.")
        return redirect("table_sessions:detail", pk=session.pk)


class SessionDetailView(WorkerRequiredMixin, DetailView):
    model = TableSession
    template_name = "table_sessions/session_detail.html"
    context_object_name = "session"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["product_form"] = SessionProductForm()
        ctx["products"] = self.object.session_products.select_related("product").all()
        ctx["products_cost"] = self.object.calculate_products_cost()
        return ctx


class SessionAddProductView(WorkerRequiredMixin, View):
    def post(self, request, pk):
        session = get_object_or_404(TableSession, pk=pk, closed_at__isnull=True)
        form = SessionProductForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data["product"]
            quantity = form.cleaned_data["quantity"]
            try:
                SessionProduct.objects.create(session=session, product=product, quantity=quantity, unit_price=product.sale_price)
                messages.success(request, f"{product.name} agregado.")
            except ValueError as e:
                messages.error(request, str(e))
        return redirect("table_sessions:detail", pk=pk)


class SessionRemoveProductView(WorkerRequiredMixin, View):
    def post(self, request, pk, item_pk):
        session = get_object_or_404(TableSession, pk=pk, closed_at__isnull=True)
        item = get_object_or_404(SessionProduct, pk=item_pk, session=session)
        name = item.product.name
        item.delete()
        messages.success(request, f"{name} eliminado.")
        return redirect("table_sessions:detail", pk=pk)


class SessionCloseView(WorkerRequiredMixin, View):
    def post(self, request, pk):
        session = get_object_or_404(TableSession, pk=pk, closed_at__isnull=True)
        try:
            session.close(worker=request.user)
            messages.success(request, f"Sesión cerrada. Total: ${session.grand_total}")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("table_sessions:list")
