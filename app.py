from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <h1>🧪 Sistema de Reagentes</h1>
    <p>✅ Funcionando com SQLite!</p>
    <p><a href="/test">Testar funcionalidade</a></p>
    '''

@app.route('/test')
def test():
    return '<h2>✅ Sistema online!</h2><p>Pr
