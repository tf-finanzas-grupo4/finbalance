# bonds/urls.py
from django.urls import path
from . import views

app_name = 'bonds'  # ¡Esto es crucial para el namespace!

urlpatterns = [
    path('', views.bond_list, name='list'),
    path('crear/', views.bond_create, name='create'),
    path('<int:bond_id>/', views.bond_detail, name='detail'),
]