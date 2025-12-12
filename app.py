from flask import Flask, request, session, redirect
from datetime import datetime
import unicodedata

app = Flask(__name__)
app.secret_key = 'reagentes-secret-2024'

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def remover_acentos(texto):
    """Remove acentos de um texto."""
    if not texto:
        return texto
    nfd = unicodedata.normalize('NFD', texto)
    sem_acentos = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    return sem_acentos

def normalizar_para_comparacao(texto):
    """Prepara texto para comparação."""
    return remover_acentos(texto).lower()

# Dados em memória
reagentes_data = [
    {'id': 1, 'nome': 'Água Destilada', 'volume_nominal': '1L', 'quantidade_embalagens': 10, 'marca': 'Synth', 'localizacao': 'Prateleira A1'},
    {'id': 2, 'nome': 'Álcool Etílico', 'volume_nominal': '500ml', 'quantidade_embalagens': 12, 'marca': 'Dinâmica', 'localizacao': 'Prateleira B2'},
    {'id': 3, 'nome': 'Ácido Clorídrico', 'volume_nominal': '250ml', 'quantidade_embalagens': 8, 'marca': 'Vetec', 'localizacao': 'Armário C3'}
]

pedidos_data = [
    {'id': 1, 'reagente': 'Sódio', 'data': '2024-08-20', 'controlado': 'Sim', 'status': 'Aberto', 'quantidade_nominal': '500g'},
    {'id': 2, 'reagente': 'Potássio', 'data': '2024-08-22', 'controlado': 'Não', 'status': 'Aberto', 'quantidade_nominal': '250g'}
]

entradas_data = []
saidas_data = []

# ============================================================================
# FUNÇÕES DE NEGÓCIO
# ============================================================================

def get_pedidos_abertos():
    return [p for p in pedidos_data if p['status'] == 'Aberto']

def finalizar_pedido(pedido_id):
    for p in pedidos_data:
        if p['id'] == pedido_id:
            p['status'] = 'Finalizado'
            break

def atualizar_reagente_quantidade(nome_reagente, volume_nominal, marca, quantidade_embalagens_adicionar, localizacao=''):
    nome_norm = normalizar_para_comparacao(nome_reagente)
    volume_norm = normalizar_para_comparacao(volume_nominal)
    marca_norm = normalizar_para_comparacao(marca)
    
    for r in reagentes_data:
        if (normalizar_para_comparacao(r['nome']) == nome_norm and 
            normalizar_para_comparacao(r.get('volume_nominal', '')) == volume_norm and
            normalizar_para_comparacao(r.get('marca', '')) == marca_norm):
            r['quantidade_embalagens'] += quantidade_embalagens_adicionar
            if localizacao:
                r['localizacao'] = localizacao
            return
    
    novo_id = max([r['id'] for r in reagentes_data]) + 1 if reagentes_data else 1
    reagentes_data.append({
        'id': novo_id,
        'nome': nome_reagente,
        'volume_nominal': volume_nominal,
        'marca': marca,
        'quantidade_embalagens': quantidade_embalagens_adicionar,
        'localizacao': localizacao or 'Não informada'
    })

def consultar_reagentes(filtro_tipo='', filtro_valor=''):
    resultados = []
    if not filtro_tipo or filtro_tipo == 'todos':
        return reagentes_data
    
    filtro_valor_norm = normalizar_para_comparacao(filtro_valor)
    
    for r in reagentes_data:
        match = False
        if filtro_tipo == 'nome':
            if filtro_valor_norm in normalizar_para_comparacao(r['nome']):
                match = True
        elif filtro_tipo == 'marca':
            if normalizar_para_comparacao(r.get('marca', '')) == filtro_valor_norm:
                match = True
        elif filtro_tipo == 'volume':
            if filtro_valor_norm in normalizar_para_comparacao(r.get('volume_nominal', '')):
                match = True
        elif filtro_tipo == 'localizacao':
            if filtro_valor_norm in normalizar_para_comparacao(r.get('localizacao', '')):
                match = True
        elif filtro_tipo == 'quantidade_min':
            try:
                if r['quantidade_embalagens'] >= int(filtro_valor):
                    match = True
            except ValueError:
                pass
        elif filtro_tipo == 'quantidade_max':
            try:
                if r['quantidade_embalagens'] <= int(filtro_valor):
                    match = True
            except ValueError:
                pass
        elif filtro_tipo == 'critico':
            if r['quantidade_embalagens'] < 5:
                match = True
        elif filtro_tipo == 'zerado':
            if r['quantidade_embalagens'] <= 0:
                match = True
        
        if match:
            resultados.append(r)
    
    return resultados

def consultar_pedidos(status='todos'):
    if status == 'abertos':
        return [p for p in pedidos_data if p['status'] == 'Aberto']
    elif status == 'recebidos':
        return [p for p in pedidos_data if p['status'] == 'Finalizado']
    else:
        return pedidos_data

def gerar_relatorio_estoque():
    total_itens = len(reagentes_data)
    total_embalagens = sum(r['quantidade_embalagens'] for r in reagentes_data)
    criticos = [r for r in reagentes_data if r['quantidade_embalagens'] < 5]
    zerados = [r for r in reagentes_data if r['quantidade_embalagens'] <= 0]
    
    return {
        'total_itens': total_itens,
        'total_embalagens': total_embalagens,
        'itens_criticos': criticos,
        'itens_zerados': zerados,
        'media_embalagens': round(total_embalagens / total_itens, 2) if total_itens > 0 else 0,
        'item_com_maior_estoque': max(reagentes_data, key=lambda x: x['quantidade_embalagens']) if reagentes_data else None
    }

def gerar_relatorio_pedidos():
    pedidos_abertos = consultar_pedidos('abertos')
    pedidos_recebidos = consultar_pedidos('recebidos')
    
    total_pedidos = len(pedidos_data)
    
    return {
        'total_pedidos': total_pedidos,
        'pedidos_abertos': pedidos_abertos,
        'pedidos_recebidos': pedidos_recebidos,
        'total_abertos': len(pedidos_abertos),
        'total_recebidos': len(pedidos_recebidos),
        'percentual_recebidos': round((len(pedidos_recebidos) / total_pedidos * 100), 1) if total_pedidos > 0 else 0
    }

def consultar_estoque_por_localizacao():
    por_localizacao = {}
    for r in reagentes_data:
        localizacao = r.get('localizacao', 'Não informada')
        if localizacao not in por_localizacao:
            por_localizacao[localizacao] = []
        por_localizacao[localizacao].append(r)
    return por_localizacao

# ============================================================================
# ROTAS
# ============================================================================

@app.route('/')
def home():
    """Home da intranet do laboratório."""
    if 'logged_in' not in session:
        return redirect('/login')
    
    return '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Intranet do Laboratório - Faculdade de Engenharia Química</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f5f5f5;
            }
            
            .header {
                background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                color: white;
                padding: 20px 40px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            
            .header-left {
                display: flex;
                align-items: center;
                gap: 20px;
            }
            
            .logo {
                font-size: 24px;
                font-weight: bold;
            }
            
            .header-title {
                border-left: 2px solid white;
                padding-left: 20px;
            }
            
            .header-title h1 {
                font-size: 20px;
                margin-bottom: 5px;
            }
            
            .header-title p {
                font-size: 12px;
                opacity: 0.9;
            }
            
            .user-info {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .user-info a {
                color: white;
                text-decoration: none;
                padding: 8px 15px;
                background: rgba(255,255,255,0.2);
                border-radius: 5px;
                transition: background 0.3s;
            }
            
            .user-info a:hover {
                background: rgba(255,255,255,0.3);
            }
            
            .nav-tabs {
                background: white;
                border-bottom: 2px solid #ecf0f1;
                padding: 0 40px;
                display: flex;
                gap: 30px;
                flex-wrap: wrap;
            }
            
            .nav-tabs a {
                padding: 15px 0;
                color: #2c3e50;
                text-decoration: none;
                border-bottom: 3px solid transparent;
                transition: all 0.3s;
                font-size: 14px;
                font-weight: 500;
            }
            
            .nav-tabs a:hover {
                color: #3498db;
                border-bottom-color: #3498db;
            }
            
            .container {
                max-width: 1400px;
                margin: 40px auto;
                padding: 0 40px;
            }
            
            .page-title {
                margin-bottom: 30px;
            }
            
            .page-title h2 {
                font-size: 28px;
                color: #2c3e50;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .services-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }
            
            .service-card {
                background: white;
                border-radius: 8px;
                padding: 25px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                transition: all 0.3s;
                cursor: pointer;
                border-left: 5px solid #3498db;
            }
            
            .service-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
            
            .service-card.reagentes {
                border-left-color: #e74c3c;
                background: linear-gradient(135deg, #fff5f5 0%, #ffe8e8 100%);
            }
            
            .service-card.pedidos {
                border-left-color: #f39c12;
                background: linear-gradient(135deg, #fffbf0 0%, #ffe8cc 100%);
            }
            
            .service-card.entradas {
                border-left-color: #27ae60;
                background: linear-gradient(135deg, #f0fff4 0%, #d5f4e6 100%);
            }
            
            .service-card.saidas {
                border-left-color: #9b59b6;
                background: linear-gradient(135deg, #faf5ff 0%, #f0e6ff 100%);
            }
            
            .service-card.relatorio {
                border-left-color: #3498db;
                background: linear-gradient(135deg, #f0f8ff 0%, #e0f2ff 100%);
            }
            
            .service-card h3 {
                font-size: 18px;
                color: #2c3e50;
                margin-bottom: 12px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .service-card p {
                color: #555;
                font-size: 14px;
                line-height: 1.6;
                margin-bottom: 15px;
            }
            
            .service-card a {
                display: inline-block;
                padding: 10px 20px;
                background: #3498db;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-size: 13px;
                font-weight: 600;
                transition: background 0.3s;
            }
            
            .service-card.reagentes a {
                background: #e74c3c;
            }
            
            .service-card.pedidos a {
                background: #f39c12;
            }
            
            .service-card.entradas a {
                background: #27ae60;
            }
            
            .service-card.saidas a {
                background: #9b59b6;
            }
            
            .service-card.relatorio a {
                background: #3498db;
            }
            
            .service-card a:hover {
                opacity: 0.9;
            }
            
            .footer {
                text-align: center;
                padding: 30px;
                color: #666;
                font-size: 12px;
                margin-top: 50px;
            }
            
            @media (max-width: 768px) {
                .header {
                    flex-direction: column;
                    gap: 15px;
                    padding: 15px;
                }
                
                .nav-tabs {
                    padding: 0 20px;
                    gap: 15px;
                }
                
                .container {
                    padding: 0 20px;
                }
                
                .services-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-left">
                <div class="logo">🔬 FEQ</div>
                <div class="header-title">
                    <h1>Faculdade de Engenharia Química</h1>
                    <p>Sistema de Gestão do Laboratório</p>
                </div>
            </div>
            <div class="user-info">
                <span>👤 Bem-vindo, admin</span>
                <a href="/logout">Sair</a>
            </div>
        </div>
        
        <div class="nav-tabs">
            <a href="/">🏠 Dashboard</a>
            <a href="/reagentes">🧪 Reagentes</a>
            <a href="/consulta">🔍 Consultas</a>
            <a href="/relatorio">📊 Relatório</a>
        </div>
        
        <div class="container">
            <div class="page-title">
                <h2>🏠 Dashboard - Intranet do Laboratório</h2>
            </div>
            
            <div class="services-grid">
                <div class="service-card reagentes">
                    <h3>🧪 Reagentes em Estoque</h3>
                    <p>Visualize e gerencie todos os reagentes disponíveis no laboratório com informações de marca, volume e localização.</p>
                    <a href="/reagentes">Acessar →</a>
                </div>
                
                <div class="service-card pedidos">
                    <h3>📝 Gerenciar Pedidos</h3>
                    <p>Crie novos pedidos de reagentes e acompanhe o status de pedidos abertos e recebidos.</p>
                    <a href="/novo-pedido">Novo Pedido →</a>
                </div>
                
                <div class="service-card entradas">
                    <h3>📦 Entrada de Reagentes</h3>
                    <p>Registre a chegada de novos reagentes no laboratório com data e localização de armazenagem.</p>
                    <a href="/entrada-reagente">Registrar Entrada →</a>
                </div>
                
                <div class="service-card saidas">
                    <h3>➖ Saída de Reagentes</h3>
                    <p>Registre a retirada de reagentes do estoque para uso em experimentos e aulas.</p>
                    <a href="/saida-reagente">Registrar Saída →</a>
                </div>
                
                <div class="service-card relatorio">
                    <h3>📊 Relatório Completo</h3>
                    <p>Visualize estatísticas de estoque, pedidos abertos, itens críticos e distribuição por localização.</p>
                    <a href="/relatorio">Ver Relatório →</a>
                </div>
                
                <div class="service-card relatorio" style="border-left-color: #16a085; background: linear-gradient(135deg, #f0fff8 0%, #d5f4f1 100%);">
                    <h3>🔍 Consultas Avançadas</h3>
                    <p>Busque reagentes, visualize pedidos abertos e recebidos com filtros avançados e múltiplas opções.</p>
                    <a href="/consulta" style="background: #16a085;">Consultar →</a>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>© 2024 Sistema de Gestão de Reagentes - Faculdade de Engenharia Química | Unicamp</p>
            <p>Desenvolvido com ❤️ para melhorar a eficiência do laboratório</p>
        </div>
    </body>
    </html>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login do sistema."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == 'admin' and password == 'admin123':
            session['logged_in'] = True
            return redirect('/')
        else:
            erro = '❌ Usuário ou senha incorretos!'
            return f'''
            <!DOCTYPE html>
            <html lang="pt-BR">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Login - Intranet do Laboratório</title>
                <style>
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}
                    
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                    }}
                    
                    .login-container {{
                        background: white;
                        padding: 50px;
                        border-radius: 10px;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                        width: 100%;
                        max-width: 400px;
                    }}
                    
                    .login-header {{
                        text-align: center;
                        margin-bottom: 40px;
                    }}
                    
                    .login-header h1 {{
                        font-size: 32px;
                        color: #2c3e50;
                        margin-bottom: 10px;
                    }}
                    
                    .login-header p {{
                        color: #666;
                        font-size: 14px;
                    }}
                    
                    .error {{
                        background: #f8d7da;
                        color: #721c24;
                        padding: 12px;
                        border-radius: 5px;
                        margin-bottom: 20px;
                        border-left: 4px solid #f5c6cb;
                    }}
                    
                    .form-group {{
                        margin-bottom: 20px;
                    }}
                    
                    .form-group label {{
                        display: block;
                        color: #2c3e50;
                        font-weight: 600;
                        margin-bottom: 8px;
                    }}
                    
                    .form-group input {{
                        width: 100%;
                        padding: 12px;
                        border: 1px solid #ddd;
                        border-radius: 5px;
                        font-size: 14px;
                        transition: border-color 0.3s;
                    }}
                    
                    .form-group input:focus {{
                        outline: none;
                        border-color: #667eea;
                        box-shadow: 0 0 5px rgba(102, 126, 234, 0.3);
                    }}
                    
                    .form-group button {{
                        width: 100%;
                        padding: 12px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        border: none;
                        border-radius: 5px;
                        font-size: 16px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: transform 0.2s;
                    }}
                    
                    .form-group button:hover {{
                        transform: translateY(-2px);
                    }}
                    
                    .credentials {{
                        background: #ecf0f1;
                        padding: 15px;
                        border-radius: 5px;
                        text-align: center;
                        font-size: 13px;
                        color: #555;
                    }}
                    
                    .credentials p {{
                        margin: 5px 0;
                    }}
                    
                    .credentials strong {{
                        color: #2c3e50;
                        font-family: monospace;
                    }}
                </style>
            </head>
            <body>
                <div class="login-container">
                    <div class="login-header">
                        <h1>🔐 Login</h1>
                        <p>Intranet do Laboratório - FEQ</p>
                    </div>
                    
                    <form method="post">
                        <div class="error">{erro}</div>
                        
                        <div class="form-group">
                            <label>Usuário:</label>
                            <input type="text" name="username" required autofocus>
                        </div>
                        
                        <div class="form-group">
                            <label>Senha:</label>
                            <input type="password" name="password" required>
                        </div>
                        
                        <div class="form-group">
                            <button type="submit">Entrar</button>
                        </div>
                    </form>
                    
                    <div class="credentials">
                        <p><strong>Credenciais de Teste:</strong></p>
                        <p>👤 Usuário: <strong>admin</strong></p>
                        <p>🔑 Senha: <strong>admin123</strong></p>
                    </div>
                </div>
            </body>
            </html>
            '''
    
    return '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login - Intranet do Laboratório</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            
            .login-container {
                background: white;
                padding: 50px;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                width: 100%;
                max-width: 400px;
            }
            
            .login-header {
                text-align: center;
                margin-bottom: 40px;
            }
            
            .login-header h1 {
                font-size: 32px;
                color: #2c3e50;
                margin-bottom: 10px;
            }
            
            .login-header p {
                color: #666;
                font-size: 14px;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            .form-group label {
                display: block;
                color: #2c3e50;
                font-weight: 600;
                margin-bottom: 8px;
            }
            
            .form-group input {
                width: 100%;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
                transition: border-color 0.3s;
            }
            
            .form-group input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 5px rgba(102, 126, 234, 0.3);
            }
            
            .form-group button {
                width: 100%;
                padding: 12px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s;
            }
            
            .form-group button:hover {
                transform: translateY(-2px);
            }
            
            .credentials {
                background: #ecf0f1;
                padding: 15px;
                border-radius: 5px;
                text-align: center;
                font-size: 13px;
                color: #555;
            }
            
            .credentials p {
                margin: 5px 0;
            }
            
            .credentials strong {
                color: #2c3e50;
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="login-header">
                <h1>🔐 Login</h1>
                <p>Intranet do Laboratório - FEQ</p>
            </div>
            
            <form method="post">
                <div class="form-group">
                    <label>Usuário:</label>
                    <input type="text" name="username" required autofocus>
                </div>
                
                <div class="form-group">
                    <label>Senha:</label>
                    <input type="password" name="password" required>
                </div>
                
                <div class="form-group">
                    <button type="submit">Entrar</button>
                </div>
            </form>
            
            <div class="credentials">
                <p><strong>Credenciais de Teste:</strong></p>
                <p>👤 Usuário: <strong>admin</strong></p>
                <p>🔑 Senha: <strong>admin123</strong></p>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/logout')
def logout():
    """Logout do sistema."""
    session.clear()
    return redirect('/login')

@app.route('/reagentes')
def reagentes():
    """Ver reagentes em estoque."""
    if 'logged_in' not in session:
        return redirect('/login')
    
    html = '<div style="margin:20px;padding:20px;">'
    html += '<h2>🧪 Reagentes em Estoque</h2>'
    html += '<table border="1" style="width:100%;border-collapse:collapse;">'
    html += '<tr style="background-color:#f0f0f0;"><th>Nome</th><th>Marca</th><th>Volume/Massa</th><th>📍 Localização</th><th>Quantidade</th></tr>'
    
    for r in reagentes_data:
        volume = r.get('volume_nominal', 'N/A')
        marca = r.get('marca', 'N/A')
        localizacao = r.get('localizacao', 'Não informada')
        html += f'<tr><td><b>{r["nome"]}</b></td><td>{marca}</td><td>{volume}</td><td><b>{localizacao}</b></td><td><b>{r["quantidade_embalagens"]}</b></td></tr>'
    
    html += '</table>'
    html += '<p style="margin-top:20px;"><a href="/">🏠 Voltar ao Menu</a></p>'
    html += '</div>'
    return html

@app.route('/consulta', methods=['GET', 'POST'])
def consulta():
    """Página de consulta com abas."""
    if 'logged_in' not in session:
        return redirect('/login')
    
    aba_ativa = request.args.get('aba', 'reagentes')
    resultados = []
    filtro_aplicado = False
    
    if request.method == 'POST':
        filtro_tipo = request.form.get('filtro_tipo', '')
        filtro_valor = request.form.get('filtro_valor', '')
        aba_ativa = request.form.get('aba', 'reagentes')
        
        if aba_ativa == 'reagentes' and filtro_tipo and filtro_valor:
            resultados = consultar_reagentes(filtro_tipo, filtro_valor)
            filtro_aplicado = True
    
    pedidos_abertos = consultar_pedidos('abertos')
    pedidos_recebidos = consultar_pedidos('recebidos')
    
    html_reagentes = '<table border="1" style="width:100%;border-collapse:collapse;">'
    html_reagentes += '<tr style="background-color:#f0f0f0;"><th>Nome</th><th>Marca</th><th>Volume/Massa</th><th>📍 Localização</th><th>Quantidade</th></tr>'
    
    if aba_ativa == 'reagentes':
        if resultados:
            for r in resultados:
                volume = r.get('volume_nominal', 'N/A')
                marca = r.get('marca', 'N/A')
                localizacao = r.get('localizacao', 'Não informada')
                qtd_cor = 'red' if r['quantidade_embalagens'] < 5 else 'green'
                html_reagentes += f'<tr><td><b>{r["nome"]}</b></td><td>{marca}</td><td>{volume}</td><td><b>{localizacao}</b></td><td style="color:{qtd_cor};"><b>{r["quantidade_embalagens"]}</b></td></tr>'
        else:
            msg = '❌ Nenhum reagente encontrado' if filtro_aplicado else 'Realize uma busca para ver resultados'
            html_reagentes += f'<tr><td colspan="5" style="text-align:center;color:{"red" if filtro_aplicado else "gray"};">{msg}</td></tr>'
    
    html_reagentes += '</table>'
    
    html_abertos = '<table border="1" style="width:100%;border-collapse:collapse;">'
    html_abertos += '<tr style="background-color:#fff3cd;"><th>Reagente</th><th>Quantidade</th><th>Data</th><th>Controlado</th><th>Status</th></tr>'
    
    if pedidos_abertos:
        for p in pedidos_abertos:
            controlado_cor = 'red' if p['controlado'] == 'Sim' else 'green'
            html_abertos += f'<tr style="background-color:#fffacd;"><td><b>{p["reagente"]}</b></td><td>{p["quantidade_nominal"]}</td><td>{p["data"]}</td><td style="color:{controlado_cor};"><b>{p["controlado"]}</b></td><td style="color:orange;"><b>⏳ {p["status"]}</b></td></tr>'
    else:
        html_abertos += '<tr><td colspan="5" style="text-align:center;color:green;">✅ Nenhum pedido aberto</td></tr>'
    
    html_abertos += '</table>'
    
    html_recebidos = '<table border="1" style="width:100%;border-collapse:collapse;">'
    html_recebidos += '<tr style="background-color:#d4edda;"><th>Reagente</th><th>Quantidade</th><th>Data</th><th>Controlado</th><th>Status</th></tr>'
    
    if pedidos_recebidos:
        for p in pedidos_recebidos:
            controlado_cor = 'red' if p['controlado'] == 'Sim' else 'green'
            html_recebidos += f'<tr style="background-color:#e8f5e9;"><td><b>{p["reagente"]}</b></td><td>{p["quantidade_nominal"]}</td><td>{p["data"]}</td><td style="color:{controlado_cor};"><b>{p["controlado"]}</b></td><td style="color:green;"><b>✅ {p["status"]}</b></td></tr>'
    else:
        html_recebidos += '<tr><td colspan="5" style="text-align:center;color:gray;">Nenhum pedido recebido ainda</td></tr>'
    
    html_recebidos += '</table>'
    
    css_aba = 'padding:12px 20px;margin-right:5px;border-radius:5px;text-decoration:none;font-weight:bold;color:white;display:inline-block;'
    
    return f'''
    <div style="max-width:900px;margin:20px;padding:20px;border:1px solid #ccc;">
        <h2>🔍 Consultas e Pedidos</h2>
        
        <div style="margin-bottom:25px;border-bottom:2px solid #ddd;padding-bottom:10px;">
            <a href="/consulta?aba=reagentes" style="{css_aba}background:{'#0066cc' if aba_ativa == 'reagentes' else '#999'};">🧪 Reagentes</a>
            <a href="/consulta?aba=abertos" style="{css_aba}background:{'#ff9800' if aba_ativa == 'abertos' else '#999'};">⏳ Pedidos Abertos ({len(pedidos_abertos)})</a>
            <a href="/consulta?aba=recebidos" style="{css_aba}background:{'#4caf50' if aba_ativa == 'recebidos' else '#999'};">✅ Pedidos Recebidos ({len(pedidos_recebidos)})</a>
        </div>
        
        {f'''<form method="post" style="margin-bottom:20px;">
            <input type="hidden" name="aba" value="reagentes">
            <p>
                <label><strong>Tipo de Filtro:</strong></label><br>
                <select name="filtro_tipo" required style="padding:8px;width:300px;">
                    <option value="">-- Selecione um filtro --</option>
                    <option value="nome">Por Nome</option>
                    <option value="marca">Por Marca</option>
                    <option value="volume">Por Volume/Massa</option>
                    <option value="localizacao">Por Localização</option>
                    <option value="quantidade_min">Quantidade Mínima</option>
                    <option value="quantidade_max">Quantidade Máxima</option>
                    <option value="critico">Estoque Crítico (&lt; 5)</option>
                    <option value="zerado">Estoque Zerado</option>
                </select>
            </p>
            
            <p>
                <label><strong>Valor do Filtro:</strong></label><br>
                <input type="text" name="filtro_valor" style="width:300px;padding:8px;" placeholder="Digite o valor de busca">
            </p>
            
            <p>
                <button type="submit" style="padding:10px 20px;background:blue;color:white;cursor:pointer;border-radius:5px;">🔍 Buscar</button>
                <button type="reset" style="padding:10px 20px;background:gray;color:white;cursor:pointer;border-radius:5px;">Limpar</button>
            </p>
        </form>''' if aba_ativa == 'reagentes' else ''}
        
        <hr>
        
        {f'<h3>Resultados de Reagentes ({len(resultados)}):</h3>{html_reagentes}' if aba_ativa == 'reagentes' else ''}
        {f'<h3>Pedidos Abertos ({len(pedidos_abertos)})</h3>{html_abertos}' if aba_ativa == 'abertos' else ''}
        {f'<h3>Pedidos Recebidos ({len(pedidos_recebidos)})</h3>{html_recebidos}' if aba_ativa == 'recebidos' else ''}
        
        <p style="margin-top:20px;"><a href="/">🏠 Voltar ao Menu</a></p>
    </div>
    '''

@app.route('/entrada-reagente', methods=['GET', 'POST'])
def entrada_reagente():
    if 'logged_in' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        data_chegada = request.form['data_chegada']
        pedido_feito = request.form['pedido_feito']
        marca = request.form['marca']
        volume_nominal = request.form['volume_nominal']
        quantidade_embalagens = int(request.form['quantidade_embalagens'])
        localizacao = request.form['localizacao']
        controlado = request.form['controlado']
        data_validade = request.form.get('data_validade', '')
        
        if pedido_feito == 'Sim':
            pedido_id = int(request.form['pedido_selecionado'])
            pedido = next((p for p in pedidos_data if p['id'] == pedido_id), None)
            if pedido:
                nome_reagente = pedido['reagente']
                finalizar_pedido(pedido_id)
        else:
            nome_reagente = request.form['nome_reagente_manual']
        
        nova_entrada = {
            'id': len(entradas_data) + 1,
            'data_chegada': data_chegada,
            'nome_reagente': nome_reagente,
            'marca': marca,
            'volume_nominal': volume_nominal,
            'quantidade_embalagens': quantidade_embalagens,
            'localizacao': localizacao,
            'controlado': controlado,
            'data_validade': data_validade,
            'pedido_origem': pedido_feito
        }
        entradas_data.append(nova_entrada)
        atualizar_reagente_quantidade(nome_reagente, volume_nominal, marca, quantidade_embalagens, localizacao)
        
        return f'''
        <h2>✅ Entrada Registrada!</h2>
        <p>Reagente: <b>{nome_reagente}</b> ({volume_nominal})</p>
        <p>Marca: <b>{marca}</b></p>
        <p>Quantidade: <b>{quantidade_embalagens} embalagens</b></p>
        <p>Localização: <b>{localizacao}</b></p>
        <p><a href="/">🏠 Voltar ao Menu</a></p>
        '''
    
    pedidos_abertos = get_pedidos_abertos()
    options_pedidos = ""
    for p in pedidos_abertos:
        options_pedidos += f'<option value="{p["id"]}">{p["reagente"]} - {p["quantidade_nominal"]}</option>'
    
    return f'''
    <div style="max-width:600px;margin:20px;padding:20px;border:1px solid #ccc;">
        <h2>📦 Entrada de Reagente</h2>
        <form method="post">
            <p>
                <label>Data de Chegada:</label><br>
                <input type="date" name="data_chegada" required style="padding:5px;">
            </p>
            
            <p>
                <label>O pedido foi feito pelo professor?</label><br>
                <select name="pedido_feito" onchange="togglePedido()" id="pedidoSelect" style="padding:5px;">
                    <option value="Sim">Sim</option>
                    <option value="Não">Não</option>
                </select>
            </p>
            
            <div id="pedidoCadastrado" style="display:block;">
                <p>
                    <label>Nome do Reagente:</label><br>
                    <select name="pedido_selecionado" style="padding:5px;width:300px;">
                        <option>Selecione o Reagente</option>
                        {options_pedidos}
                    </select>
                </p>
            </div>
            
            <div id="pedidoManual" style="display:none;">
                <p>
                    <label>Nome do Reagente:</label><br>
                    <input type="text" name="nome_reagente_manual" style="width:300px;padding:5px;">
                </p>
            </div>
            
            <p>
                <label>Marca:</label><br>
                <input type="text" name="marca" required style="width:300px;padding:5px;">
            </p>
            
            <p>
                <label>Volume Nominal:</label><br>
                <input type="text" name="volume_nominal" placeholder="Ex: 500ml, 1L" required style="width:200px;padding:5px;">
            </p>
            
            <p>
                <label>Quantidade de Embalagens:</label><br>
                <input type="number" name="quantidade_embalagens" min="1" required style="width:100px;padding:5px;">
            </p>
            
            <p>
                <label>📍 Localização:</label><br>
                <input type="text" name="localizacao" placeholder="Ex: Prateleira A1" required style="width:300px;padding:5px;">
            </p>
            
            <p>
                <label>Controlado?</label><br>
                <select name="controlado" style="padding:5px;">
                    <option value="Sim">Sim</option>
                    <option value="Não" selected>Não</option>
                </select>
            </p>
            
            <p>
                <label>Data de Validade:</label><br>
                <input type="date" name="data_validade" style="padding:5px;">
            </p>
            
            <p>
                <button type="submit" style="padding:8px 15px;background:green;color:white;">Salvar</button>
                <button type="reset" style="padding:8px 15px;background:gray;color:white;">Fechar</button>
            </p>
        </form>
        <p><a href="/">🏠 Voltar</a></p>
    </div>
    
    <script>
    function togglePedido() {{
        var select = document.getElementById('pedidoSelect');
        var cadastrado = document.getElementById('pedidoCadastrado');
        var manual = document.getElementById('pedidoManual');
        
        if (select.value === 'Sim') {{
            cadastrado.style.display = 'block';
            manual.style.display = 'none';
        }} else {{
            cadastrado.style.display = 'none';
            manual.style.display = 'block';
        }}
    }}
    </script>
    '''

@app.route('/saida-reagente', methods=['GET', 'POST'])
def saida_reagente():
    if 'logged_in' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        nome_reagente = request.form['nome_reagente']
        marca = request.form['marca']
        volume_nominal = request.form['volume_nominal']
        quantidade_saida = int(request.form['quantidade'])
        
        nome_norm = normalizar_para_comparacao(nome_reagente)
        marca_norm = normalizar_para_comparacao(marca)
        volume_norm = normalizar_para_comparacao(volume_nominal)
        
        reagente_encontrado = None
        for r in reagentes_data:
            if (normalizar_para_comparacao(r['nome']) == nome_norm and 
                normalizar_para_comparacao(r.get('marca', '')) == marca_norm and
                normalizar_para_comparacao(r.get('volume_nominal', '')) == volume_norm):
                reagente_encontrado = r
                break
        
        if not reagente_encontrado:
            return '''<h2>❌ Erro!</h2><p>Reagente não encontrado.</p><p><a href="/saida-reagente">Tentar novamente</a></p><p><a href="/">Voltar</a></p>'''
        
        if quantidade_saida > reagente_encontrado['quantidade_embalagens']:
            return f'''<h2>❌ Quantidade Insuficiente!</h2><p>Disponível: {reagente_encontrado['quantidade_embalagens']}</p><p>Solicitado: {quantidade_saida}</p><p><a href="/saida-reagente">Tentar novamente</a></p>'''
        
        nova_saida = {
            'id': len(saidas_data) + 1,
            'data_saida': datetime.now().strftime('%Y-%m-%d'),
            'nome_reagente': reagente_encontrado['nome'],
            'marca': reagente_encontrado.get('marca', 'N/A'),
            'volume_nominal': reagente_encontrado.get('volume_nominal', 'N/A'),
            'quantidade_saida': quantidade_saida,
            'usuario': 'admin',
            'localizacao': reagente_encontrado.get('localizacao', 'N/A')
        }
        saidas_data.append(nova_saida)
        reagente_encontrado['quantidade_embalagens'] -= quantidade_saida
        
        if reagente_encontrado['quantidade_embalagens'] <= 0:
            reagentes_data.remove(reagente_encontrado)
            status_estoque = "❌ Reagente ZERADO"
        else:
            status_estoque = f"✅ Restam {reagente_encontrado['quantidade_embalagens']}"
        
        return f'''
        <h2>✅ Saída Registrada!</h2>
        <p>Reagente: <b>{reagente_encontrado['nome']}</b></p>
        <p>Quantidade: <b>{quantidade_saida} embalagens</b></p>
        <p>{status_estoque}</p>
        <p><a href="/">🏠 Voltar</a></p>
        '''
    
    reagentes_js = str(reagentes_data).replace("'", '"')
    
    return f'''
    <div style="max-width:500px;margin:20px;padding:20px;border:1px solid #ccc;">
        <h2>➖ Saída de Reagente</h2>
        <form method="post">
            <p>
                <label>Nome:</label><br>
                <input type="text" name="nome_reagente" id="nomeReagente" oninput="buscarMarcas()" required style="width:300px;padding:5px;">
            </p>
            
            <p>
                <label>Marca:</label><br>
                <select name="marca" id="marcaSelect" onchange="buscarVolumes()" required style="padding:5px;width:200px;">
                    <option>Selecione uma marca</option>
                </select>
            </p>
            
            <p>
                <label>Volume:</label><br>
                <select name="volume_nominal" id="volumeSelect" required style="padding:5px;width:200px;">
                    <option>Selecione um volume</option>
                </select>
            </p>
            
            <p>
                <label>Quantidade:</label><br>
                <input type="number" name="quantidade" min="1" required style="width:100px;padding:5px;">
            </p>
            
            <p>
                <button type="submit" style="padding:8px 15px;background:red;color:white;">Registrar Saída</button>
            </p>
        </form>
        <p><a href="/">🏠 Voltar</a></p>
    </div>
    
    <script>
    var reagentes = {reagentes_js};
    
    function buscarMarcas() {{
        var nome = document.getElementById('nomeReagente').value.toLowerCase();
        var marcaSelect = document.getElementById('marcaSelect');
        marcaSelect.innerHTML = '<option>Selecione uma marca</option>';
        
        var marcas = [];
        reagentes.forEach(function(r) {{
            if (r.nome.toLowerCase().includes(nome)) {{
                var marca = r.marca || 'N/A';
                if (marcas.indexOf(marca) === -1) {{
                    marcas.push(marca);
                    var opt = document.createElement('option');
                    opt.value = marca;
                    opt.text = marca;
                    marcaSelect.add(opt);
                }}
            }}
        }});
    }}
    
    function buscarVolumes() {{
        var nome = document.getElementById('nomeReagente').value.toLowerCase();
        var marca = document.getElementById('marcaSelect').value;
        var volumeSelect = document.getElementById('volumeSelect');
        volumeSelect.innerHTML = '<option>Selecione um volume</option>';
        
        reagentes.forEach(function(r) {{
            if (r.nome.toLowerCase().includes(nome) && (r.marca || 'N/A') === marca) {{
                var opt = document.createElement('option');
                opt.value = r.volume_nominal;
                opt.text = r.volume_nominal + ' (' + r.quantidade_embalagens + ' disponíveis)';
                volumeSelect.add(opt);
            }}
        }});
    }}
    </script>
    '''

@app.route('/novo-pedido', methods=['GET', 'POST'])
def novo_pedido():
    if 'logged_in' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        nome_reagente = request.form['nome_reagente']
        data_pedido = request.form['data_pedido']
        controlado = request.form['controlado']
        quantidade_nominal = request.form['quantidade_nominal']
        
        novo_pedido = {
            'id': len(pedidos_data) + 1,
            'reagente': nome_reagente,
            'data': data_pedido,
            'controlado': controlado,
            'quantidade_nominal': quantidade_nominal,
            'status': 'Aberto'
        }
        pedidos_data.append(novo_pedido)
        
        return f'<h2>✅ Pedido Criado!</h2><p>Reagente: <b>{nome_reagente}</b></p><p><a href="/pedidos">Ver Pedidos</a></p><p><a href="/">Voltar</a></p>'
    
    return '''
    <div style="max-width:500px;margin:20px;padding:20px;border:1px solid #ccc;">
        <h2>📝 Novo Pedido</h2>
        <form method="post">
            <p>
                <label>Nome:</label><br>
                <input type="text" name="nome_reagente" required style="width:300px;padding:5px;">
            </p>
            <p>
                <label>Quantidade:</label><br>
                <input type="text" name="quantidade_nominal" required style="width:200px;padding:5px;">
            </p>
            <p>
                <label>Data:</label><br>
                <input type="date" name="data_pedido" required style="padding:5px;">
            </p>
            <p>
                <label>Controlado?</label><br>
                <select name="controlado" style="padding:5px;">
                    <option value="Sim">Sim</option>
                    <option value="Não" selected>Não</option>
                </select>
            </p>
            <p>
                <button type="submit" style="padding:8px 15px;background:green;color:white;">Salvar</button>
            </p>
        </form>
        <p><a href="/">Voltar</a></p>
    </div>
    '''

@app.route('/pedidos')
def pedidos():
    if 'logged_in' not in session:
        return redirect('/login')
    
    html = '<div style="margin:20px;padding:20px;"><h2>📝 Pedidos</h2><table border="1" style="width:100%;border-collapse:collapse;"><tr><th>ID</th><th>Reagente</th><th>Qtd</th><th>Data</th><th>Controlado</th><th>Status</th></tr>'
    
    for p in pedidos_data:
        status_cor = 'green' if p['status'] == 'Finalizado' else 'orange'
        controlado_cor = 'red' if p['controlado'] == 'Sim' else 'green'
        html += f'<tr><td>#{p["id"]}</td><td><b>{p["reagente"]}</b></td><td>{p["quantidade_nominal"]}</td><td>{p["data"]}</td><td style="color:{controlado_cor};">{p["controlado"]}</td><td style="color:{status_cor};">{p["status"]}</td></tr>'
    
    html += '</table><p style="margin-top:20px;"><a href="/novo-pedido">Novo Pedido</a></p><p><a href="/">Voltar</a></p></div>'
    return html

@app.route('/relatorio')
def relatorio():
    if 'logged_in' not in session:
        return redirect('/login')
    
    rel_estoque = gerar_relatorio_estoque()
    rel_pedidos = gerar_relatorio_pedidos()
    
    html = f'''
    <div style="margin:20px;padding:20px;">
        <h2>📊 Relatório Completo</h2>
        <h3>Estoque:</h3>
        <p>Total de Itens: <b>{rel_estoque["total_itens"]}</b></p>
        <p>Total de Embalagens: <b>{rel_estoque["total_embalagens"]}</b></p>
        <p>Média: <b>{rel_estoque["media_embalagens"]}</b></p>
        
        <h3>Pedidos:</h3>
        <p>Abertos: <b>{rel_pedidos["total_abertos"]}</b></p>
        <p>Recebidos: <b>{rel_pedidos["total_recebidos"]}</b></p>
        
        <h3>Itens Críticos (&lt; 5):</h3>
        {len(rel_estoque["itens_criticos"])} item(ns)
        
        <p><a href="/">Voltar</a></p>
    </div>
    '''
    return html

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
