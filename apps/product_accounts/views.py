from django.views.generic import ListView, CreateView, DetailView, View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from apps.core.mixins import WorkerRequiredMixin
from apps.products.models import Product
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

    def form_valid(self, form):
        form.instance.worker = self.request.user
        account = form.save()
        messages.success(self.request, 'Cuenta creada.')
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
        return ctx


class AccountAddProductView(WorkerRequiredMixin, View):
    def post(self, request, pk):
        account = get_object_or_404(ProductAccount, pk=pk, closed_at__isnull=True)
        product_id = request.POST.get('product')
        quantity = int(request.POST.get('quantity', 1))
        try:
            product = Product.objects.get(pk=product_id)
            AccountProduct.objects.create(account=account, product=product, quantity=quantity, unit_price=product.sale_price)
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
    """
    Recibe paid=1 (pago) o paid=0 (queda debiendo).
    """
    def post(self, request, pk):
        account = get_object_or_404(ProductAccount, pk=pk, closed_at__isnull=True)
        paid = request.POST.get('paid', '1') == '1'
        try:
            account.close(worker=request.user, paid=paid)
            if paid:
                messages.success(request, f'Cuenta cerrada y cobrada. Total: ${account.grand_total}')
            else:
                messages.warning(request, f'Cuenta cerrada. ${account.grand_total} quedaron como cuenta por cobrar.')
        except ValueError as e:
            messages.error(request, str(e))
        return redirect('product_accounts:list')
