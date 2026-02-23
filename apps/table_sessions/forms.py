from django import forms
from apps.clients.models import Client
from apps.tables.models import Table
from apps.products.models import Product
from .models import TableSession, SessionProduct


class TableSessionForm(forms.ModelForm):
    class Meta:
        model = TableSession
        fields = ['table', 'client', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['table'].queryset = Table.objects.filter(is_active=True)
        self.fields['client'].queryset = Client.objects.filter(is_active=True)


class SessionProductForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True, stock__gt=0),
        label='Producto'
    )
    quantity = forms.IntegerField(min_value=1, initial=1, label='Cantidad')
