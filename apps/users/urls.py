from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', views.UserListView.as_view(), name='list'),
    path('crear/', views.UserCreateView.as_view(), name='create'),
    path('<int:pk>/editar/', views.UserUpdateView.as_view(), name='update'),
]
