from django.urls import path
from . import views

urlpatterns = [
    # 1. URL de Login (Nome CRUCIAL para o decorator: LOGIN_URL_NAME = 'do_login')
    path('', views.meu_login_view, name='login'), 
    path('login/', views.meu_login_view, name='login'), 


    # 2. URL de Redirecionamento para DAF (Nome CRUCIAL para o views.py)
    path('dashboard/daf/', views.view_daf, name='home_daf'), 
    # 3. URL de Redirecionamento para GSTR (Nome CRUCIAL para o views.py)
    path('dashboard/gstr/', views.view_gstr, name='home_gstr'),
    # 4. URL da Home Padrão (Nome CRUCIAL para o fallback no views.py e no decorator)
    path('dashboard/home/', views.view_home, name='home'),
    # 5.
    path('dashboard/admin/', views.view_admin, name='home_admin'),



    path('requerimento/novo/', views.inserir_requisicao, name='inserir_requisicao'),

    path('requisicoes', views.view_usuario, name='home_user')
]

