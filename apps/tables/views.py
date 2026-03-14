from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from apps.core.mixins import AdminRequiredMixin, WorkerRequiredMixin
from .models import Table
from .forms import TableForm


class TableListView(WorkerRequiredMixin, ListView):
    model = Table
    template_name = 'tables/table_list.html'
    context_object_name = 'tables'
    queryset = Table.objects.filter(is_active=True)


class TableDetailView(WorkerRequiredMixin, DetailView):
    model = Table
    template_name = 'tables/table_detail.html'
    context_object_name = 'table'


class TableCreateView(AdminRequiredMixin, CreateView):
    model = Table
    form_class = TableForm
    template_name = 'tables/table_form.html'
    success_url = reverse_lazy('tables:list')

    def form_valid(self, form):
     messages.success(self.request, 'Mesa creada correctamente.')
     return super().form_valid(form)


class TableUpdateView(AdminRequiredMixin, UpdateView):
    model = Table
    form_class = TableForm
    template_name = 'tables/table_form.html'
    success_url = reverse_lazy('tables:list')

    def form_valid(self, form):
        messages.success(self.request, 'Mesa actualizada correctamente.')
        return super().form_valid(form)
