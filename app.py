from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '<h1>🧪 Sistema Funcionando!</h1><p>SQLite OK!</p>'

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
