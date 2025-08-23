from flask import Flask, request, session, redirect
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'reagentes-secret-2024'

def init_db():
    conn = sqlite3.connect('reagentes.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS reagentes 
                    (id INTEGER PRIMARY KEY, nome TEXT, quantidade REAL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS pedidos 
                    (id INTEGER PRIMARY KEY, reagente TEXT, data TEXT, status TEXT)''')
    conn.commit()
    conn.close()

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
    
    conn = sqlite3.connect('reagentes.db')
    reagentes = conn.execute('SELECT * FROM reagentes').fetchall()
    conn.close()
    
    html = '<h2>🧪 Reagentes</h2><ul>'
    for r in reagentes:
        html += f'<li>{r[1]} - Qtd: {r[2]}</li>'
    html += '</ul><a href="/">Voltar</a>'
    return html

@app.route('/pedidos')
def pedidos():
    if 'logged_in' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect('reagentes.db')
    pedidos = conn.execute('SELECT * FROM pedidos').fetchall()
    conn.close()
    
    html = '<h2>📝 Pedidos</h2><ul>'
    for p in pedidos:
        html += f'<li>{p[1]} - {p[2]} - Status: {p[3]}</li>'
    html += '</ul><a href="/">Voltar</a>'
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
    <form method="post">
        <h2>🔐 Login</h2>
        Usuário: <input name="username" required><br><br>
        Senha: <input type="password" name="password" required><br><br>
        <button>Entrar</button>
    </form>
    <p>Use: admin / admin123</p>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
