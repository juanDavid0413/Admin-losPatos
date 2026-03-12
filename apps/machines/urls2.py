from django.urls import path
from . import views

app_name = 'machines'

urlpatterns = [
    path('', views.MachineListView.as_view(), name='list'),
    path('crear/', views.MachineCreateView.as_view(), name='create'),
    path('pago/', views.MachinePaymentView.as_view(), name='payment'),
]