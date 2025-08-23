from flask import Flask, request, session, redirect

app = Flask(__name__)
app.secret_key = 'reagentes-secret-2024'

# Dados em memória (temporário)
reagentes_data = [
    {'nome': 'Água Destilada', 'quantidade': 10.5},
    {'nome': 'Álcool Etílico', 'quantidade': 5.0},
    {'nome': 'Ácido Clorídrico', 'quantidade': 2.5}
]

pedidos_data = [
    {'reagente': 'Sódio', 'data': '2024-08-20', 'status': 'Pendente'},
    {'reagente': 'Potássio', 'data': '2024-08-22', 'status': 'Entregue'}
]

@app.route('/')
def home():
    if 'logged_in' not in session:
        return redirect('/login')
    
    return '''
    <h1>🧪 Sistema de Reagentes</h1>
    <p>✅ Logado como: admin</p>
    <p><a href="/reagentes">📋 Ver Reagentes</a></p>
    <p><a href="/pedidos">📝 Ver Pedidos</a></p>
    <p><a href="/logout">Sair</a></p>
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
        html += f'<li><b>{p["reagente"]}</b> - {p["data"]} - Status: <em>{p["status"]}</em></li>'
    html += '</ul><p><a href="/">🏠 Voltar</a></p>'
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
