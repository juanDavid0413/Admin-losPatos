from django.views.generic import ListView, CreateView, DetailView, View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from apps.core.mixins import WorkerRequiredMixin
from apps.products.models import Product
from apps.clients.models import Client
from .models import ProductAccount, AccountProduct


class ProductAccountListView(WorkerRequiredMixin, ListView):
    model = ProductAccount
    template_name = 'product_accounts/account_list.html'
    context_object_name = 'accounts'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['open_accounts'] = ProductAccount.objects.select_related(
            'client', 'worker'
        ).filter(closed_at__isnull=True).order_by('-opened_at')
        ctx['closed_accounts'] = ProductAccount.objects.select_related(
            'client', 'worker'
        ).filter(closed_at__isnull=False).order_by('-closed_at')[:30]
        return ctx


class ProductAccountCreateView(WorkerRequiredMixin, CreateView):
    model = ProductAccount
    fields = ['client', 'notes']
    template_name = 'product_accounts/account_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['clients'] = Client.objects.filter(is_active=True).order_by('name')
        return ctx

    def form_valid(self, form):
        account = form.save(commit=False)
        account.worker = self.request.user

        # Alias para cliente de paso
        alias = self.request.POST.get('walkup_alias', '').strip()
        if alias and 'de paso' in account.client.name.lower():
            prefix = f'[Alias: {alias}] '
            account.notes = prefix + (account.notes or '')

        account.save()
        label = f'"{alias}"' if alias else account.client.name
        messages.success(self.request, f'Cuenta abierta para {label}.')
        return redirect('product_accounts:detail', pk=account.pk)


class ProductAccountDetailView(WorkerRequiredMixin, DetailView):
    model = ProductAccount
    template_name = 'product_accounts/account_detail.html'
    context_object_name = 'account'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['products_list'] = self.object.account_products.select_related('product').all()
        ctx['total'] = self.object.calculate_total()
        ctx['available_products'] = Product.objects.filter(is_active=True, stock__gt=0)

        # Extraer alias si aplica
        alias = ''
        notes = self.object.notes or ''
        if notes.startswith('[Alias:'):
            alias = notes.split(']')[0].replace('[Alias:', '').strip()
        ctx['walkup_alias'] = alias
        return ctx


class AccountAddProductView(WorkerRequiredMixin, View):
    def post(self, request, pk):
        account = get_object_or_404(ProductAccount, pk=pk, closed_at__isnull=True)
        product_id = request.POST.get('product')
        quantity = int(request.POST.get('quantity', 1))
        try:
            product = Product.objects.get(pk=product_id)
            AccountProduct.objects.create(
                account=account, product=product,
                quantity=quantity, unit_price=product.sale_price
            )
            messages.success(request, f'{product.name} agregado.')
        except Exception as e:
            messages.error(request, str(e))
        return redirect('product_accounts:detail', pk=pk)


class AccountRemoveProductView(WorkerRequiredMixin, View):
    def post(self, request, pk, item_pk):
        account = get_object_or_404(ProductAccount, pk=pk, closed_at__isnull=True)
        item = get_object_or_404(AccountProduct, pk=item_pk, account=account)
        name = item.product.name
        item.delete()
        messages.success(request, f'{name} eliminado.')
        return redirect('product_accounts:detail', pk=pk)


class ProductAccountCloseView(WorkerRequiredMixin, View):
    def post(self, request, pk):
        account = get_object_or_404(ProductAccount, pk=pk, closed_at__isnull=True)
        paid = request.POST.get('paid', '1') == '1'
        try:
            account.close(worker=request.user, paid=paid)
            if paid:
                messages.success(request, f'Cuenta cerrada y cobrada. Total: ${account.grand_total}')
            else:
                messages.warning(request, f'Cuenta cerrada. ${account.grand_total} en cuentas por cobrar.')
        except ValueError as e:
            messages.error(request, str(e))
        return redirect('product_accounts:list')
