from flask import Flask, request, session, redirect
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = 'reagentes-secret-2024'

# Dados em memória
reagentes_data = [
    {'id': 1, 'nome': 'Água Destilada', 'volume_nominal': '1L', 'quantidade_total': 10.5, 'tipo_unidade': 'volume'},
    {'id': 2, 'nome': 'Álcool Etílico', 'volume_nominal': '500ml', 'quantidade_total': 5.0, 'tipo_unidade': 'volume'},
    {'id': 3, 'nome': 'Ácido Clorídrico', 'volume_nominal': '250ml', 'quantidade_total': 2.5, 'tipo_unidade': 'volume'}
]

pedidos_data = [
    {'id': 1, 'reagente': 'Sódio', 'data': '2024-08-20', 'controlado': 'Sim', 'status': 'Aberto', 'quantidade_nominal': '500g'},
    {'id': 2, 'reagente': 'Potássio', 'data': '2024-08-22', 'controlado': 'Não', 'status': 'Aberto', 'quantidade_nominal': '250g'}
]

entradas_data = []

def detectar_tipo_unidade(volume_nominal):
    """Detecta se é volume (L) ou massa (g)"""
    unidade = volume_nominal.lower()
    
    # Unidades de volume
    if any(u in unidade for u in ['ml', 'l', 'ul', 'dl', 'cl']):
        return 'volume'
    
    # Unidades de massa
    if any(u in unidade for u in ['g', 'kg', 'mg', 'ug']):
        return 'massa'
    
    # Default: assumir volume
    return 'volume'

def converter_para_unidade_base(volume_nominal, quantidade_embalagens):
    """Converte para unidade base: L para volume, g para massa"""
    try:
        # Extrair número
        numeros = re.findall(r'\d+\.?\d*', volume_nominal.replace(',', '.'))
        if not numeros:
            return quantidade_embalagens, 'unidade'
        
        valor = float(numeros[0])
        unidade = volume_nominal.lower().replace(str(valor), '').replace(',', '').replace('.', '').strip()
        
        # CONVERSÕES DE VOLUME (para Litros)
        conversoes_volume = {
            'ul': 0.000001,  # microlitro
            'ml': 0.001,     # mililitro
            'cl': 0.01,      # centilitro
            'dl': 0.1,       # decilitro
            'l': 1.0,        # litro
        }
        
        # CONVERSÕES DE MASSA (para gramas)
        conversoes_massa = {
            'ug': 0.000001,  # micrograma
            'mg': 0.001,     # miligrama
            'g': 1.0,        # grama
            'kg': 1000.0,    # quilograma
        }
        
        # Detectar tipo
        if any(u in unidade for u in conversoes_volume.keys()):
            # É volume - converter para L
            fator = conversoes_volume.get(unidade, 1.0)
            total = valor * fator * quantidade_embalagens
            return total, 'L'
            
        elif any(u in unidade for u in conversoes_massa.keys()):
            # É massa - converter para g
            fator = conversoes_massa.get(unidade, 1.0)
            total = valor * fator * quantidade_embalagens
            return total, 'g'
        
        # Fallback
        return valor * quantidade_embalagens, unidade
        
    except:
        return quantidade_embalagens, 'unidade'

def get_pedidos_abertos():
    return [p for p in pedidos_data if p['status'] == 'Aberto']

def finalizar_pedido(pedido_id):
    for p in pedidos_data:
        if p['id'] == pedido_id:
            p['status'] = 'Finalizado'
            break

def atualizar_reagente_quantidade(nome_reagente, volume_nominal, quantidade_adicionar, tipo_unidade, unidade_base):
    for r in reagentes_data:
        if (r['nome'].lower() == nome_reagente.lower() and 
            r.get('volume_nominal', '').lower() == volume_nominal.lower()):
            r['quantidade_total'] += quantidade_adicionar
            return
    
    novo_id = max([r['id'] for r in reagentes_data]) + 1 if reagentes_data else 1
    reagentes_data.append({
        'id': novo_id,
        'nome': nome_reagente,
        'volume_nominal': volume_nominal,
        'quantidade_total': quantidade_adicionar,
        'tipo_unidade': tipo_unidade,
        'unidade_base': unidade_base
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
        controlado = request.form['controlado']
        data_validade = request.form.get('data_validade', '')
        
        # Calcular quantidade total com conversão correta
        quantidade_total, unidade_base = converter_para_unidade_base(volume_nominal, quantidade_embalagens)
        tipo_unidade = detectar_tipo_unidade(volume_nominal)
        
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
            'quantidade_total': quantidade_total,
            'unidade_base': unidade_base,
            'localizacao': localizacao,
            'controlado': controlado,
            'data_validade': data_validade,
            'pedido_origem': pedido_feito
        }
        entradas_data.append(nova_entrada)
        
        atualizar_reagente_quantidade(nome_reagente, volume_nominal, quantidade_total, tipo_unidade, unidade_base)
        
        return f'''
        <h2>✅ Entrada Registrada!</h2>
        <p>Reagente: {nome_reagente} ({volume_nominal})</p>
        <p>Quantidade: {quantidade_embalagens} embalagens</p>
        <p>Total: {quantidade_total:.2f} {unidade_base}</p>
        <p>Localização: {localizacao}</p>
        <p><a href="/entradas">Ver Todas as Entradas</a></p>
        <p><a href="/reagentes">Ver Reagentes Atualizados</a></p>
        <p><a href="/">Voltar ao Menu</a></p>
        '''
    
    pedidos_abertos = get_pedidos_abertos()
    
    # Criar options de pedidos
    options_pedidos = ""
    for p in pedidos_abertos:
        options_pedidos += f'<option value="{p["id"]}">{p["reagente"]} - {p["quantidade_nominal"]}</option>'
    
    return f'''
    <div style="max-width:600px;margin:20px;padding:20px;border:1px solid #ccc;">
        <h2>Entrada de Reagente</h2>
        <form method="post" id="entradaForm">
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
                    <label>Nome do Reagente (Caso Não Seja Pedido):</label><br>
                    <input type="text" name="nome_reagente_manual" style="width:300px;padding:5px;">
                </p>
            </div>
            
            <p>
                <label>Marca:</label><br>
                <input type="text" name="marca" required style="width:300px;padding:5px;">
            </p>
            
            <p>
                <label>Volume Nominal da Embalagem:</label><br>
                <input type="text" name="volume_nominal" placeholder="Ex: 500ml, 1L, 250g, 2kg" required style="width:200px;padding:5px;">
                <br><small style="color:blue;">💡 Volume: ul, ml, cl, dl, L | Massa: ug, mg, g, kg</small>
            </p>
            
            <p>
                <label>Quantidade de Embalagens:</label><br>
                <input type="number" name="quantidade_embalagens" min="1" required style="width:100px;padding:5px;">
            </p>
            
            <p>
                <label>Localização:</label><br>
                <input type="text" name="localizacao" required style="width:300px;padding:5px;">
            </p>
            
            <p>
                <label>Reagente Controlado?</label><br>
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

@app.route('/entradas')
def entradas():
    if 'logged_in' not in session:
        return redirect('/login')
    
    html = '<h2>📦 Entradas de Reagentes</h2>'
    html += '<table border="1" style="width:100%;border-collapse:collapse;">'
    html += '<tr><th>Data</th><th>Reagente</th><th>Volume/Massa</th><th>Marca</th><th>Qtd Emb.</th><th>Total</th><th>Localização</th><th>Validade</th></tr>'
    
    for e in entradas_data:
        validade = e.get('data_validade', '') or 'N/A'
        unidade = e.get('unidade_base', 'unidade')
        html += f'<tr>'
        html += f'<td>{e["data_chegada"]}</td>'
        html += f'<td><b>{e["nome_reagente"]}</b></td>'
        html += f'<td>{e["volume_nominal"]}</td>'
        html += f'<td>{e["marca"]}</td>'
        html += f'<td>{e["quantidade_embalagens"]}</td>'
        html += f'<td>{e["quantidade_total"]:.2f} {unidade}</td>'
        html += f'<td>{e["localizacao"]}</td>'
        html += f'<td>{validade}</td>'
        html += f'</tr>'
    
    html += '</table>'
    html += '<p><a href="/entrada-reagente">➕ Nova Entrada</a></p>'
    html += '<p><a href="/">🏠 Voltar</a></p>'
    return html

@app.route('/reagentes')
def reagentes():
    if 'logged_in' not in session:
        return redirect('/login')
    
    html = '<h2>🧪 Reagentes em Estoque</h2>'
    html += '<p><small>📊 Volumes em <strong>L</strong> | Massas em <strong>g</strong></small></p>'
    html += '<table border="1" style="width:100%;border-collapse:collapse;">'
    html += '<tr><th>Nome</th><th>Volume/Massa Nominal</th><th>Quantidade Total</th><th>Tipo</th></tr>'
    
    for r in reagentes_data:
        volume = r.get('volume_nominal', 'N/A')
        unidade_base = r.get('unidade_base', 'L')
        tipo_unidade = r.get('tipo_unidade', 'volume')
        
        # Ícone baseado no tipo
        icone_tipo = '🧪' if tipo_unidade == 'volume' else '⚖️'
        
        html += f'<tr>'
        html += f'<td><b>{r["nome"]}</b></td>'
        html += f'<td>{volume}</td>'
        html += f'<td><strong>{r["quantidade_total"]:.2f} {unidade_base}</strong></td>'
        html += f'<td>{icone_tipo} {tipo_unidade.title()}</td>'
        html += f'</tr>'
    
    html += '</table>'
    html += '<p><small>💡 <strong>L</strong> = Litros | <strong>g</strong> = Gramas</small></p>'
    html += '<p><a href="/">🏠 Voltar</a></p>'
    return html

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
        
        return f'''
        <h2>✅ Pedido Criado!</h2>
        <p>Reagente: {nome_reagente}</p>
        <p>Quantidade: {quantidade_nominal}</p>
        <p>Data: {data_pedido}</p>
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
                <label>Quantidade Nominal:</label><br>
                <input type="text" name="quantidade_nominal" placeholder="Ex: 500ml, 1L, 250g, 2kg" required style="width:200px;padding:5px;">
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

@app.route('/pedidos')
def pedidos():
    if 'logged_in' not in session:
        return redirect('/login')
    
    html = '<h2>📝 Pedidos de Reagentes</h2>'
    html += '<table border="1" style="width:100%;border-collapse:collapse;">'
    html += '<tr><th>Reagente</th><th>Quantidade</th><th>Data</th><th>Controlado</th><th>Status</th></tr>'
    
    for p in pedidos_data:
        status_cor = 'green' if p['status'] == 'Finalizado' else 'orange'
        html += f'<tr>'
        html += f'<td><b>{p["reagente"]}</b></td>'
        html += f'<td>{p["quantidade_nominal"]}</td>'
        html += f'<td>{p["data"]}</td>'
        html += f'<td>{p["controlado"]}</td>'
        html += f'<td style="color:{status_cor}"><em>{p["status"]}</em></td>'
        html += f'</tr>'
    
    html += '</table>'
    html += '<p><a href="/novo-pedido">➕ Novo Pedido</a></p>'
    html += '<p><a href="/">🏠 Voltar</a></p>'
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
    
