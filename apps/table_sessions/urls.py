from django.urls import path
from . import views

app_name = 'table_sessions'

urlpatterns = [
    path('', views.SessionListView.as_view(), name='list'),
    path('abrir/', views.SessionOpenView.as_view(), name='open'),
    path('<int:pk>/', views.SessionDetailView.as_view(), name='detail'),
    path('<int:pk>/agregar-producto/', views.SessionAddProductView.as_view(), name='add_product'),
    path('<int:pk>/eliminar-producto/<int:item_pk>/', views.SessionRemoveProductView.as_view(), name='remove_product'),
    path('<int:pk>/cerrar/', views.SessionCloseView.as_view(), name='close'),
]
