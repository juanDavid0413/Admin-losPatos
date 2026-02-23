from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='list'),
    path('crear/', views.ProductCreateView.as_view(), name='create'),
    path('<int:pk>/editar/', views.ProductUpdateView.as_view(), name='update'),
]
