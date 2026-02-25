from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class Receivable(models.Model):
    SOURCE_SESSION = 'sesion'
    SOURCE_ACCOUNT = 'cuenta'
    SOURCE_CHOICES = [
        (SOURCE_SESSION, 'Sesion de Mesa'),
        (SOURCE_ACCOUNT, 'Cuenta de Productos'),
    ]

    STATUS_PENDING = 'pendiente'
    STATUS_PAID = 'pagada'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente'),
        (STATUS_PAID, 'Pagada'),
    ]

    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, verbose_name='Origen')
    table_session = models.OneToOneField(
        'table_sessions.TableSession', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='receivable', verbose_name='Sesion de mesa'
    )
    product_account = models.OneToOneField(
        'product_accounts.ProductAccount', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='receivable', verbose_name='Cuenta de productos'
    )
    client = models.ForeignKey(
        'clients.Client', on_delete=models.SET_NULL, null=True,
        related_name='receivables', verbose_name='Cliente'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Monto original')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'), verbose_name='Total abonado')
    notes = models.TextField(blank=True, verbose_name='Notas')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name='Estado')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Fecha de deuda')
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de pago total')
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='receivables_collected', verbose_name='Cobrado por'
    )

    class Meta:
        verbose_name = 'Cuenta por Cobrar'
        verbose_name_plural = 'Cuentas por Cobrar'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.client} — ${self.balance} pendiente'

    @property
    def is_pending(self):
        return self.status == self.STATUS_PENDING

    @property
    def balance(self):
        """Lo que falta por pagar."""
        return self.amount - self.amount_paid

    def apply_payment(self, amount, worker):
        """
        Registra un abono parcial o total.
        - Suma al amount_paid
        - Registra movimiento de ingreso inmediato
        - Si balance llega a 0, cierra la deuda
        """
        from apps.movements.models import Movement
        from apps.core.constants import MovementType, MovementSource

        amount = Decimal(str(amount)).quantize(Decimal('1'), rounding='ROUND_HALF_UP')

        if amount <= 0:
            raise ValueError('El abono debe ser mayor a cero.')
        balance_int = self.balance.quantize(Decimal('1'), rounding='ROUND_HALF_UP')
        if amount > balance_int:
            raise ValueError(f'El abono (${amount}) supera el saldo pendiente (${balance_int}).')
        # Si queda diferencia de centavos, ajustar al balance exacto
        if amount >= balance_int:
            amount = self.balance
        if not self.is_pending:
            raise ValueError('Esta deuda ya esta saldada.')

        self.amount_paid += amount
        if self.balance <= 0:
            self.status = self.STATUS_PAID
            self.paid_at = timezone.now()
            self.paid_by = worker
        self.save()

        # Determinar origen para el movimiento
        if self.source == self.SOURCE_SESSION:
            mv_source = MovementSource.TABLE_SESSION
            desc = f'Abono deuda — Mesa {self.table_session.table.name if self.table_session else "?"} — {self.client.name}'
            session_ref = self.table_session
            account_ref = None
        else:
            mv_source = MovementSource.PRODUCT_ACCOUNT
            desc = f'Abono deuda — Cuenta productos — {self.client.name}'
            session_ref = None
            account_ref = self.product_account

        if self.status == self.STATUS_PAID:
            desc = desc.replace('Abono', 'Pago total')

        Movement.objects.create(
            movement_type=MovementType.INCOME,
            source=mv_source,
            amount=amount,
            description=desc,
            table_session=session_ref,
            product_account=account_ref,
            worker=worker,
        )

        return self


class ReceivablePayment(models.Model):
    """Historial de cada abono realizado a una deuda."""
    receivable = models.ForeignKey(
        Receivable, on_delete=models.CASCADE,
        related_name='payments', verbose_name='Deuda'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Monto abonado')
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, verbose_name='Registrado por'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')
    notes = models.TextField(blank=True, verbose_name='Notas')

    class Meta:
        verbose_name = 'Abono'
        verbose_name_plural = 'Abonos'
        ordering = ['-created_at']

    def __str__(self):
        return f'Abono ${self.amount} a {self.receivable}'
