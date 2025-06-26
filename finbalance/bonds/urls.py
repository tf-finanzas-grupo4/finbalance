from django.urls import path
from . import views

app_name = 'bonds'

urlpatterns = [
    path('', views.bond_list, name='list'),
]
