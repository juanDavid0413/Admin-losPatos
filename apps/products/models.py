from django.db import models


class Product(models.Model):
    """
    Productos del billar (bebidas, snacks, etc.)
    El stock se descuenta al agregar el producto a una sesión o cuenta.
    """
    name = models.CharField(max_length=100, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio de venta')
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio de costo')
    stock = models.PositiveIntegerField(default=0, verbose_name='Stock')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} (${self.sale_price})'

    def has_stock(self, quantity=1):
        """Verifica si hay suficiente stock antes de descontar."""
        return self.stock >= quantity

    def discount_stock(self, quantity=1):
        """
        Descuenta el stock. Si no hay suficiente, lanza ValueError.
        Regla del documento: 'Si no hay stock → error'
        """
        if not self.has_stock(quantity):
            raise ValueError(f'Stock insuficiente para {self.name}. Stock actual: {self.stock}')
        self.stock -= quantity
        self.save(update_fields=['stock', 'updated_at'])

    def restore_stock(self, quantity=1):
        """Restaura stock si se cancela/elimina un item."""
        self.stock += quantity
        self.save(update_fields=['stock', 'updated_at'])
