"""
Constantes y Choices globales del proyecto.
Centralizar aquí evita strings mágicos dispersos por el código.
"""

# ── Estados de Mesa ─────────────────────────────────────────
class TableStatus:
    FREE = 'libre'
    OCCUPIED = 'ocupada'

    CHOICES = [
        (FREE, 'Libre'),
        (OCCUPIED, 'Ocupada'),
    ]

# ── Tipos de Movimiento Económico ────────────────────────────
class MovementType:
    INCOME = 'ingreso'
    EXPENSE = 'egreso'

    CHOICES = [
        (INCOME, 'Ingreso'),
        (EXPENSE, 'Egreso'),
    ]

# ── Origen del Movimiento ────────────────────────────────────
class MovementSource:
    TABLE_SESSION = 'sesion_mesa'
    PRODUCT_ACCOUNT = 'cuenta_producto'
    MACHINE = 'maquina'
    OTHER = 'otro'

    CHOICES = [
        (TABLE_SESSION, 'Sesión de Mesa'),
        (PRODUCT_ACCOUNT, 'Cuenta de Productos'),
        (MACHINE, 'Máquina'),
        (OTHER, 'Otro'),
    ]

# ── Roles de Usuario ─────────────────────────────────────────
class UserRole:
    ADMIN = 'admin'
    WORKER = 'trabajador'

    CHOICES = [
        (ADMIN, 'Administrador'),
        (WORKER, 'Trabajador'),
    ]
