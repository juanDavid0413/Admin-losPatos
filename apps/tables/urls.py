from django.urls import path
from . import views

app_name = 'tables'

urlpatterns = [
    path('', views.TableListView.as_view(), name='list'),
    path('crear/', views.TableCreateView.as_view(), name='create'),
    path('<int:pk>/', views.TableDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.TableUpdateView.as_view(), name='update'),
]
