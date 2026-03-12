from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('usuarios/', include('apps.users.urls')),
    path('clientes/', include('apps.clients.urls')),
    path('productos/', include('apps.products.urls')),
    path('mesas/', include('apps.tables.urls')),
    path('sesiones/', include('apps.table_sessions.urls')),
    path('cuentas/', include('apps.product_accounts.urls')),
    path('maquinas/', include('apps.machines.urls')),
    path('movimientos/', include('apps.movements.urls')),
    path('stock/', include('apps.stock_entries.urls')),
    path('cuentas-por-cobrar/', include('apps.receivables.urls')),
    path('informes/', include('apps.reports.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
