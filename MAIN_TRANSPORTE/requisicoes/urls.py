from django.urls import path
from . import views

app_name = 'requisicoes'

urlpatterns = [
    path('', views.principal_view, name='principal'),
]