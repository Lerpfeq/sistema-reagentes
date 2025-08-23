from flask import Flask, request, session, redirect
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'reagentes-secret-2024'

# Dados em memória
reagentes_data = [
    {'id': 1, 'nome': 'Água Destilada', 'quantidade': 10.5},
    {'id': 2, 'nome': 'Álcool Etílico', 'quantidade': 5.0},
    {'id': 3, 'nome': 'Ácido Clorídrico', 'quantidade': 2.5}
]

pedidos_data = []

@app.route('/')
def home():
    if 'logged_in' not in session:
        return redirect('/login')
    
    return '''
    <h1>🧪 Sistema de Reagentes</h1>
    <p>✅ Logado como: admin</p>
    <p><a href="/reagentes">📋 Ver Reagentes</a></p>
    <p><a href="/pedidos">📝 Ver Pedidos</a></p>
    <p><a href="/novo-pedido">➕ Novo Pedido</a></p>
    <p><a href="/logout">Sair</a></p>
    '''

@app.route('/novo-pedido', methods=['GET', 'POST'])
def novo_pedido():
    if 'logged_in' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        nome_reagente = request.form['nome_reagente']
        data_pedido = request.form['data_pedido']
        controlado = request.form['controlado']
        
        novo_pedido = {
            'id': len(pedidos_data) + 1,
            'reagente': nome_reagente,
            'data': data_pedido,
            'controlado': controlado,
            'status': 'Pendente'
        }
        pedidos_data.append(novo_pedido)
        
        return f'''
        <h2>✅ Pedido Criado!</h2>
        <p>Reagente: {nome_reagente}</p>
        <p>Data: {data_pedido}</p>
        <p>Controlado: {controlado}</p>
        <p><a href="/pedidos">Ver Todos os Pedidos</a></p>
        <p><a href="/">Voltar ao Menu</a></p>
        '''
    
    return '''
    <div style="max-width:500px;margin:20px;padding:20px;border:1px solid #ccc;">
        <h2>Pedido de Reagente</h2>
        <form method="post">
            <p>
                <label>Nome do Reagente:</label><br>
                <input type="text" name="nome_reagente" required style="width:300px;padding:5px;">
            </p>
            <p>
                <label>Data do Pedido:</label><br>
                <input type="date" name="data_pedido" required style="padding:5px;">
            </p>
            <p>
                <label>Reagente Controlado?</label><br>
                <select name="controlado" style="padding:5px;">
                    <option value="Sim">Sim</option>
                    <option value="Não" selected>Não</option>
                </select>
            </p>
            <p>
                <button type="submit" style="padding:8px 15px;background:green;color:white;">Salvar</button>
                <button type="reset" style="padding:8px 15px;background:gray;color:white;">Fechar</button>
            </p>
        </form>
        <p><a href="/">🏠 Voltar</a></p>
    </div>
    '''

@app.route('/reagentes')
def reagentes():
    if 'logged_in' not in session:
        return redirect('/login')
    
    html = '<h2>🧪 Reagentes em Estoque</h2><ul>'
    for r in reagentes_data:
        html += f'<li><b>{r["nome"]}</b> - Quantidade: {r["quantidade"]}L</li>'
    html += '</ul><p><a href="/">🏠 Voltar</a></p>'
    return html

@app.route('/pedidos')
def pedidos():
    if 'logged_in' not in session:
        return redirect('/login')
    
    html = '<h2>📝 Pedidos de Reagentes</h2><ul>'
    for p in pedidos_data:
        html += f'<li><b>{p["reagente"]}</b> - {p["data"]} - Controlado: {p["controlado"]} - Status: <em>{p["status"]}</em></li>'
    html += '</ul><p><a href="/novo-pedido">➕ Novo Pedido</a></p><p><a href="/">🏠 Voltar</a></p>'
    return html

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == 'admin' and password == 'admin123':
            session['logged_in'] = True
            return redirect('/')
    
    return '''
    <div style="max-width:400px;margin:50px auto;padding:20px;border:1px solid #ccc;">
        <form method="post">
            <h2>🔐 Login Sistema</h2>
            <p>Usuário: <input name="username" required style="width:100%;padding:5px;"></p>
            <p>Senha: <input type="password" name="password" required style="width:100%;padding:5px;"></p>
            <button style="width:100%;padding:10px;background:blue;color:white;">Entrar</button>
        </form>
        <p><small>Use: admin / admin123</small></p>
    </div>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
