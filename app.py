from flask import Flask, request, session, redirect

app = Flask(__name__)
app.secret_key = 'reagentes-secret-2024'

@app.route('/')
def home():
    if 'logged_in' in session:
        return f'''
        <h1>🧪 Sistema de Reagentes</h1>
        <p>✅ Logado como: {session.get('username', 'Usuario')}</p>
        <a href="/logout">Sair</a>
        '''
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == 'admin' and password == 'admin123':
            session['logged_in'] = True
            session['username'] = 'admin'
            return redirect('/')
    
    return '''
    <form method="post">
        <h2>Login</h2>
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
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
