from django.db import models
from django.conf import settings


class StockEntry(models.Model):
    """
    Registro de entrada de stock (compra / reposición).
    Inmutable — al crear, suma la cantidad al stock del producto.
    """
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='stock_entries',
        verbose_name='Producto'
    )
    quantity = models.PositiveIntegerField(verbose_name='Cantidad ingresada')
    stock_before = models.PositiveIntegerField(verbose_name='Stock antes')
    stock_after = models.PositiveIntegerField(verbose_name='Stock después')
    notes = models.TextField(blank=True, verbose_name='Notas / Proveedor')
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Registrado por'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')

    class Meta:
        verbose_name = 'Entrada de Stock'
        verbose_name_plural = 'Entradas de Stock'
        ordering = ['-created_at']

    def __str__(self):
        fecha = self.created_at.strftime('%d/%m/%Y')
        return f'+{self.quantity} {self.product.name} ({fecha})'

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError('Las entradas de stock son inmutables.')
        self.stock_before = self.product.stock
        self.stock_after = self.stock_before + self.quantity
        self.product.stock = self.stock_after
        self.product.save(update_fields=['stock', 'updated_at'])
        super().save(*args, **kwargs)