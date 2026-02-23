from django.urls import path
from . import views

app_name = 'movements'

urlpatterns = [
    path('', views.MovementListView.as_view(), name='list'),
    path('<int:pk>/', views.MovementDetailView.as_view(), name='detail'),
]
