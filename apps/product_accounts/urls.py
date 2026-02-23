from django.urls import path
from . import views

app_name = 'product_accounts'

urlpatterns = [
    path('', views.ProductAccountListView.as_view(), name='list'),
    path('crear/', views.ProductAccountCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ProductAccountDetailView.as_view(), name='detail'),
    path('<int:pk>/cerrar/', views.ProductAccountCloseView.as_view(), name='close'),
    path('<int:pk>/agregar/', views.AccountAddProductView.as_view(), name='add_product'),
    path('<int:pk>/eliminar/<int:item_pk>/', views.AccountRemoveProductView.as_view(), name='remove_product'),
]
