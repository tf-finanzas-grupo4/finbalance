from django.urls import path
from . import views

app_name = 'bonds'

urlpatterns = [
    path('', views.bond_list, name='list'),
    path('create/', views.bond_create, name='create'),
    path('<int:bond_id>/', views.bond_detail, name='detail'),
]
