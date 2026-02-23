from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from apps.core.mixins import WorkerRequiredMixin
from apps.products.models import Product
from .models import StockEntry


class StockEntryListView(WorkerRequiredMixin, ListView):
    model = StockEntry
    template_name = "stock_entries/stock_list.html"
    context_object_name = "entries"

    def get_queryset(self):
        return (
            StockEntry.objects
            .select_related("product", "worker")
            .order_by("-created_at")[:100]
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["products"] = Product.objects.filter(is_active=True).order_by("name")
        return ctx


class StockEntryCreateView(WorkerRequiredMixin, CreateView):
    model = StockEntry
    fields = ["product", "quantity", "notes"]
    template_name = "stock_entries/stock_form.html"
    success_url = reverse_lazy("stock_entries:list")

    def form_valid(self, form):
        entry = form.save(commit=False)
        entry.worker = self.request.user
        entry.save()

        messages.success(
            self.request,
            f"✅ Entrada registrada: +{entry.quantity} unidades de {entry.product.name}. "
            f"Stock actual: {entry.stock_after}"
        )

        self.object = entry
        return redirect(self.success_url)