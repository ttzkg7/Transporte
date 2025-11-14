from django.shortcuts import redirect
from django.urls import reverse
from functools import wraps

# 🎯 Mantenha este nome igual ao 'name' da URL de login no seu urls.py
LOGIN_URL_NAME = 'login'

def permissao_por_setor(setores_permitidos):
    """
    Decorator que verifica se o usuário está logado E se o seu setor 
    (armazenado na sessão) está na lista de setores permitidos.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            
            is_logged_in = request.session.get('is_authenticated', False)
            user_setor = request.session.get('user_setor')
            
            # 1. Verifica se o usuário está logado
            if not is_logged_in:
                # Redireciona para o login, passando a URL atual no 'next'
                path = request.build_absolute_uri()
                redirect_url = f"{reverse(LOGIN_URL_NAME)}?next={path}"
                return redirect(redirect_url)
            
            # 2. Verifica a permissão do setor
            # Converte ambos para minúsculas para evitar erros de case
            setores_permitidos_lower = [s.lower() for s in setores_permitidos]
            
            if user_setor and user_setor.lower() in setores_permitidos_lower:
                # Permissão concedida
                return view_func(request, *args, **kwargs)
            else:
                # Redireciona para a página de "Acesso Negado" (Home)
                print(f"ACESSO NEGADO: Usuário de setor '{user_setor}' tentou acessar área restrita.")
                # Assumindo que você tem uma URL chamada 'home'
                return redirect('home') 

        return wrapper
    return decorator

# --- Decorator de Login Simples ---
def meu_login_required(view_func):
    """
    Decorator personalizado para verificar se o usuário está autenticado
    (sem checagem de setor), usando as chaves de sessão definidas.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        is_logged_in = request.session.get('is_authenticated', False)
        
        if is_logged_in:
            return view_func(request, *args, **kwargs)
        else:
            # Redireciona para a URL de login com o 'next'
            path = request.build_absolute_uri()
            redirect_url = f"{reverse(LOGIN_URL_NAME)}?next={path}"
            return redirect(redirect_url)
            
    return wrapper