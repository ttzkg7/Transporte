from django.shortcuts import render, redirect
from django.db import connection
from django.urls import reverse
from .decorators import meu_login_required, permissao_por_setor
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger # 🎯 NOVA IMPORTAÇÃO

@meu_login_required 
def view_usuario(request): 
    
    nome_usuario = request.session.get('user_name', 'DESCONHECIDO')
    requisicoes_full_list = [] # Renomeado para melhor clareza
    
    # Prepara o filtro em maiúsculas
    nome_usuario_filtrado = nome_usuario.upper()
    
    # Consulta ao Banco de Dados (Busca TODOS os resultados)
    if nome_usuario_filtrado and nome_usuario_filtrado != 'DESCONHECIDO':
        try:
            with connection.cursor() as cursor:
                sql_query = """
                    SELECT id_req, itinerario, data, hora, qtd_pass, obs, status_daf, status_gstr
                    FROM requisicoes
                    WHERE usuario = %s  
                    ORDER BY data DESC, hora DESC
                """
                cursor.execute(sql_query, [nome_usuario_filtrado])
                requisicoes_full_list = cursor.fetchall() 
                
        except Exception as e:
            print(f"ERRO DE CONSULTA NO BD: {e}")
    
    # Cria o Paginator, definindo 5 itens por página
    paginator = Paginator(requisicoes_full_list, 5) 
    
    # Pega o número da página na URL (ex: ?page=2). O padrão é 1.
    page = request.GET.get('page') 
    
    try:
        # 3 Obtém a lista de itens da página solicitada
        lista_requisicoes_page = paginator.page(page)
    except PageNotAnInteger:
        # Se o número da página não for inteiro, mostra a primeira página
        lista_requisicoes_page = paginator.page(1)
    except EmptyPage:
        # Se a página estiver fora do intervalo (ex: página 99 de 10), mostra a última
        lista_requisicoes_page = paginator.page(paginator.num_pages)


    # Preparar o Contexto
    contexto = {
        'user': nome_usuario, 
        'setor': request.session.get('user_setor'),
        'total_requisicoes': len(requisicoes_full_list),  # Total geral continua útil para o CARD
        
        # Passa o objeto da PÁGINA, não a lista completa
        'lista_requisicoes': lista_requisicoes_page,       
    }

    return render(request, 'core/home_user.html', contexto)

def obter_todos_setores():
    """Busca todos os nomes de setores na tabela 'setores'."""
    setores = []
    try:
        with connection.cursor() as cursor:
            sql_query = "SELECT nome_setor FROM setores" 
            cursor.execute(sql_query)
            # cursor.fetchall() retorna uma lista de tuplas (ex: [('DAF',), ('GSTR',), ...])
            resultados = cursor.fetchall()
            
            # Extrai apenas o nome do setor da tupla
            setores = [row[0] for row in resultados if row[0] is not None]
            
    except Exception as e:
        # Se houver erro de conexão ou tabela (ex: durante o primeiro runserver) 
        print(f"ATENÇÃO: Não foi possível carregar setores do BD. Usando fallback. Erro: {e}") 
        # Retorna uma lista de setores conhecidos como fallback 
        setores = ['DAF', 'GSTR', 'PADRAO', 'FINANCEIRO', 'GEAI'] 
        
    return setores

SETORES_PERMITIDOS = obter_todos_setores()

# A view precisa estar protegida para garantir que a sessão 'user_name' exista
@permissao_por_setor(setores_permitidos=SETORES_PERMITIDOS)
def inserir_requisicao(request):
    if request.method == 'POST':
        # 1. Extrair os dados do formulário (POST)
        itinerario = request.POST.get('itinerario')
        data_req = request.POST.get('data_requisicao')
        hora_req = request.POST.get('hora_requisicao')
        passageiros = request.POST.get('passageiros')
        # Nome do campo no HTML: 'info_adicional' | Nome da coluna no BD: 'obs'
        obs = request.POST.get('info_adicional') 
        
        # 2. Dados internos (Sessão e Status Fixo)
        # Nome do colaborador logado, que está na sessão (armazenado durante o login)
        nome_usuario = request.session.get('user_name', 'DESCONHECIDO') 
        
        # O status deve ser fixo como 0 (Reprovado/Pendente) na inserção
        status_inicial_gstr = 0 
        status_inicial_daf = 0 
        
        try:
            # 3. Executar a inserção no banco de dados
            with connection.cursor() as cursor:
                sql_insert = """
                    INSERT INTO requisicoes (itinerario, data, hora, qtd_pass, obs, usuario, status_daf, status_gstr)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                # 4. Mapeamento dos valores para a query
                valores = [
                    itinerario, 
                    data_req, 
                    hora_req, 
                    passageiros, 
                    obs, 
                    nome_usuario, # <--- Fonte: Sessão
                    status_inicial_daf, # <--- Fonte: Fixo (0)
                    status_inicial_gstr # <--- Fonte: Fixo (0)
                ]
                
                cursor.execute(sql_insert, valores)
                
            # 5. Redirecionar após o sucesso
            # Redireciona para a dashboard do usuário comum (Exemplo)
            return redirect(reverse('home')) 
            
        except Exception as e:
            # Em caso de erro, trate
            print(f"ERRO DE INSERÇÃO NO BD: {e}")
            # Você precisa renderizar o template do formulário novamente
            return render(request, 'core/home_user.html', {'error': f'Erro ao salvar: {e}'})
            
    # Se for GET, renderiza o formulário (Assumindo que o formulário está neste template)
    return render(request, 'core/home_user.html')

# --- View de Login com Redirecionamento por Setor ---
def meu_login_view(request):
    """
    Processa o login, armazena a sessão e redireciona 
    para a URL do setor do usuário.
    """
    if request.method == 'POST':
        username_or_email = request.POST.get('email')
        password_input = request.POST.get('password') 

        # 1. Autenticação (Ainda usando a checagem insegura de senha no SQL, como solicitado)
        with connection.cursor() as cursor:
            sql_query = """
                SELECT id_user, nome, setor 
                FROM user 
                WHERE email = %s AND senha = %s
            """
            cursor.execute(sql_query, [username_or_email, password_input])
            row = cursor.fetchone() 

        if row:
            user_id, user_name, user_setor = row 
            
            # Armazena na sessão
            request.session['user_id'] = user_id
            request.session['is_authenticated'] = True
            request.session['user_name'] = user_name 
            request.session['user_setor'] = user_setor 
            
            # 2. Lógica de Redirecionamento Baseada no Setor
            setor = user_setor.upper() if user_setor else ''

            if setor == 'DAF':
                # Redireciona usando o NAME='home_daf' do urls.py
                return redirect(reverse('home_daf'))
            
            elif setor == 'GSTR':
                # Redireciona usando o NAME='home_gstr' do urls.py
                return redirect(reverse('home_gstr'))
                
            elif setor == 'ADMIN':
                return redirect(reverse('home_admin'))
                
            else:
                # Redirecionamento padrão (fallback)
                return redirect(reverse('home')) 

        # Credenciais inválidas
        return render(request, 'core/login.html', {'error': 'Credenciais inválidas.'})

    return render(request, 'core/login.html')


# --- Views Protegidas pelos Decorators ---

# 1. View Exclusiva para o Setor DAF
@permissao_por_setor(setores_permitidos=['DAF'])
def view_daf(request):
    return render(request, 'core/home_daf.html', {'setor': 'DAF'})

# 2. View Exclusiva para o Setor GSTR
@permissao_por_setor(setores_permitidos=['GSTR'])
def view_gstr(request):
    return render(request, 'core/home_gstr.html', {'setor': 'GSTR'})

# 2. View Exclusiva para o Setor ADMIN
@permissao_por_setor(setores_permitidos=['ADMIN'])
def view_admin(request):
    return render(request, 'core/home_admin.html', {'setor': 'ADMIN'})

# 3. View que só exige Login (Home Padrão)
@meu_login_required
def view_home(request):
    return render(request, 'core/home_user.html', {'user': request.session.get('user_name')})