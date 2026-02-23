from django.urls import path
from . import views

app_name = 'receivables'

urlpatterns = [
    path('', views.ReceivableListView.as_view(), name='list'),
    path('<int:pk>/abonar/', views.ReceivableApplyPaymentView.as_view(), name='apply_payment'),
]
