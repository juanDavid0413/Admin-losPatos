from django.views.generic import ListView, CreateView, UpdateView
from apps.core.mixins import WorkerRequiredMixin, AdminRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Product


class ProductListView(WorkerRequiredMixin, ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'


class ProductCreateView(AdminRequiredMixin, CreateView):
    model = Product
    fields = ['name', 'description', 'sale_price', 'cost_price', 'stock', 'is_active']
    template_name = 'products/form.html'
    success_url = reverse_lazy('products:list')

    def form_valid(self, form):
        messages.success(self.request, 'Producto guardado correctamente.')
        return super().form_valid(form)


class ProductUpdateView(AdminRequiredMixin, UpdateView):
    model = Product
    fields = ['name', 'description', 'sale_price', 'cost_price', 'stock', 'is_active']
    template_name = 'products/form.html'
    success_url = reverse_lazy('products:list')

    def form_valid(self, form):
        messages.success(self.request, 'Producto actualizado correctamente.')
        return super().form_valid(form)
