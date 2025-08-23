from flask import Flask, request, session, redirect
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'reagentes-secret-2024'

# Dados em memória
reagentes_data = [
    {'id': 1, 'nome': 'Água Destilada', 'volume_nominal': '1L', 'quantidade_total': 10.5},
    {'id': 2, 'nome': 'Álcool Etílico', 'volume_nominal': '500ml', 'quantidade_total': 5.0},
    {'id': 3, 'nome': 'Ácido Clorídrico', 'volume_nominal': '250ml', 'quantidade_total': 2.5}
]

pedidos_data = [
    {'id': 1, 'reagente': 'Sódio', 'data': '2024-08-20', 'controlado': 'Sim', 'status': 'Aberto', 'quantidade_nominal': '500g'},
    {'id': 2, 'reagente': 'Potássio', 'data': '2024-08-22', 'controlado': 'Não', 'status': 'Aberto', 'quantidade_nominal': '250g'}
]

entradas_data = []

def get_pedidos_abertos():
    return [p for p in pedidos_data if p['status'] == 'Aberto']

def finalizar_pedido(pedido_id):
    for p in pedidos_data:
        if p['id'] == pedido_id:
            p['status'] = 'Finalizado'
            break

def atualizar_reagente_quantidade(nome_reagente, volume_nominal, quantidade_adicionar):
    # Procura reagente existente COM MESMO NOME E MESMO VOLUME
    for r in reagentes_data:
        if (r['nome'].lower() == nome_reagente.lower() and 
            r.get('volume_nominal', '').lower() == volume_nominal.lower()):
            r['quantidade_total'] += quantidade_adicionar
            return
    
    # Se não existe essa combinação específica, cria novo registro
    novo_id = max([r['id'] for r in reagentes_data]) + 1 if reagentes_data else 1
    reagentes_data.append({
        'id': novo_id,
        'nome': nome_reagente,
        'volume_nominal': volume_nominal,
        'quantidade_total': quantidade_adicionar
    })

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
    <p><a href="/entrada-reagente">📦 Entrada de Reagente</a></p>
    <p><a href="/entradas">📋 Ver Entradas</a></p>
    <p><a href="/logout">Sair</a></p>
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
        controlado = request.form
