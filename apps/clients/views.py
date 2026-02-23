from django.views.generic import ListView, CreateView, UpdateView
from apps.core.mixins import WorkerRequiredMixin, AdminRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Client


class ClientListView(WorkerRequiredMixin, ListView):
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'


class ClientCreateView(AdminRequiredMixin, CreateView):
    model = Client
    fields = ['name', 'phone', 'email', 'notes', 'is_active']
    template_name = 'clients/form.html'
    success_url = reverse_lazy('clients:list')

    def form_valid(self, form):
        messages.success(self.request, 'Cliente guardado correctamente.')
        return super().form_valid(form)


class ClientUpdateView(AdminRequiredMixin, UpdateView):
    model = Client
    fields = ['name', 'phone', 'email', 'notes', 'is_active']
    template_name = 'clients/form.html'
    success_url = reverse_lazy('clients:list')

    def form_valid(self, form):
        messages.success(self.request, 'Cliente actualizado correctamente.')
        return super().form_valid(form)
