from flask import Flask, request, session, redirect
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'reagentes-secret-2024'

# Dados em memória
reagentes_data = [
    {'id': 1, 'nome': 'Água Destilada', 'volume_nominal': '1L', 'quantidade_embalagens': 10, 'marca': 'Synth'},
    {'id': 2, 'nome': 'Álcool Etílico', 'volume_nominal': '500ml', 'quantidade_embalagens': 12, 'marca': 'Dinâmica'},
    {'id': 3, 'nome': 'Ácido Clorídrico', 'volume_nominal': '250ml', 'quantidade_embalagens': 8, 'marca': 'Vetec'}
]

pedidos_data = [
    {'id': 1, 'reagente': 'Sódio', 'data': '2024-08-20', 'controlado': 'Sim', 'status': 'Aberto', 'quantidade_nominal': '500g'},
    {'id': 2, 'reagente': 'Potássio', 'data': '2024-08-22', 'controlado': 'Não', 'status': 'Aberto', 'quantidade_nominal': '250g'}
]

entradas_data = []
saidas_data = []

def get_pedidos_abertos():
    return [p for p in pedidos_data if p['status'] == 'Aberto']

def finalizar_pedido(pedido_id):
    for p in pedidos_data:
        if p['id'] == pedido_id:
            p['status'] = 'Finalizado'
            break

def atualizar_reagente_quantidade(nome_reagente, volume_nominal, marca, quantidade_embalagens_adicionar):
    # Procura reagente existente COM MESMO NOME, VOLUME E MARCA
    for r in reagentes_data:
        if (r['nome'].lower() == nome_reagente.lower() and 
            r.get('volume_nominal', '').lower() == volume_nominal.lower() and
            r.get('marca', '').lower() == marca.lower()):
            r['quantidade_embalagens'] += quantidade_embalagens_adicionar
            return
    
    # Se não existe essa combinação específica, cria novo registro
    novo_id = max([r['id'] for r in reagentes_data]) + 1 if reagentes_data else 1
    reagentes_data.append({
        'id': novo_id,
        'nome': nome_reagente,
        'volume_nominal': volume_nominal,
        'marca': marca,
        'quantidade_embalagens': quantidade_embalagens_adicionar
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
    <p><a href="/saida-reagente">➖ Saída de Reagente</a></p>
    <p><a href="/saidas">📤 Ver Saídas</a></p>
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
        
        # Atualizar quantidade do reagente (incluindo marca)
        atualizar_reagente_quantidade(nome_reagente, volume_nominal, marca, quantidade_embalagens)
        
        return f'''
        <h2>✅ Entrada Registrada!</h2>
        <p>Reagente: <b>{nome_reagente}</b> ({volume_nominal})</p>
        <p>Marca: <b>{marca}</b></p>
        <p>Quantidade: <b>{quantidade_embalagens} embalagens</b></p>
        <p>Localização: {localizacao}</p>
        <p><a href="/entradas">📋 Ver Todas as Entradas</a></p>
        <p><a href="/reagentes">🧪 Ver Reagentes Atualizados</a></p>
        <p><a href="/">🏠 Voltar ao Menu</a></p>
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
                <br><small style="color:blue;">💡 Reagentes só somam se Nome + Volume + Marca forem iguais</small>
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

@app.route('/saida-reagente', methods=['GET', 'POST'])
def saida_reagente():
    if 'logged_in' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        nome_reagente = request.form['nome_reagente']
        marca = request.form['marca']
        volume_nominal = request.form['volume_nominal']
        quantidade_saida = int(request.form['quantidade'])
        
        # Buscar reagente específico (nome + marca + volume)
        reagente_encontrado = None
        for r in reagentes_data:
            if (r['nome'].lower() == nome_reagente.lower() and 
                r.get('marca', '').lower() == marca.lower() and
                r.get('volume_nominal', '').lower() == volume_nominal.lower()):
                reagente_encontrado = r
                break
        
        if not reagente_encontrado:
            return f'''
            <h2>❌ Erro!</h2>
            <p>Reagente não encontrado no estoque.</p>
            <p><a href="/saida-reagente">Tentar novamente</a></p>
            <p><a href="/">Voltar ao Menu</a></p>
            '''
        
        # Verificar se tem quantidade suficiente
        if quantidade_saida > reagente_encontrado['quantidade_embalagens']:
            return f'''
            <h2>❌ Quantidade Insuficiente!</h2>
            <p>Reagente: <b>{nome_reagente}</b></p>
            <p>Marca: <b>{marca}</b> - Volume: <b>{volume_nominal}</b></p>
            <p>Disponível: <b>{reagente_encontrado['quantidade_embalagens']} embalagens</b></p>
            <p>Solicitado: <b>{quantidade_saida} embalagens</b></p>
            <p><a href="/saida-reagente">Tentar novamente</a></p>
            <p><a href="/">Voltar ao Menu</a></p>
            '''
        
        # Registrar saída
        nova_saida = {
            'id': len(saidas_data) + 1,
            'data_saida': datetime.now().strftime('%Y-%m-%d'),
            'nome_reagente': nome_reagente,
            'marca': marca,
            'volume_nominal': volume_nominal,
            'quantidade_saida': quantidade_saida,
            'usuario': 'admin'
        }
        saidas_data.append(nova_saida)
        
        # Abater do estoque
        reagente_encontrado['quantidade_embalagens'] -= quantidade_saida
        
        # Se zerou, remover do estoque
        if reagente_encontrado['quantidade_embalagens'] <= 0:
            reagentes_data.remove(reagente_encontrado)
            status_estoque = "❌ Reagente ZERADO - Removido do estoque"
        else:
            status_estoque = f"✅ Restam {reagente_encontrado['quantidade_embalagens']} embalagens"
        
        return f'''
        <h2>✅ Saída Registrada!</h2>
        <p>Reagente: <b>{nome_reagente}</b></p>
        <p>Marca: <b>{marca}</b></p>
        <p>Volume: <b>{volume_nominal}</b></p>
        <p>Quantidade retirada: <b>{quantidade_saida} embalagens</b></p>
        <p>{status_estoque}</p>
        <p><a href="/saidas">📤 Ver Todas as Saídas</a></p>
        <p><a href="/reagentes">🧪 Ver Estoque Atualizado</a></p>
        <p><a href="/">🏠 Voltar ao Menu</a></p>
        '''
    
    # Criar dados JavaScript dos reagentes para busca dinâmica
    reagentes_js = str(reagentes_data).replace("'", '"')
    
    return f'''
    <div style="max-width:500px;margin:20px;padding:20px;border:1px solid #ccc;">
        <h2>Saída de Reagente</h2>
        <form method="post" id="saidaForm">
            <p>
                <label>Nome do Reagente:</label><br>
                <input type="text" name="nome_reagente" id="nomeReagente" oninput="buscarMarcas()" required style="width:300px;padding:5px;">
            </p>
            
            <p>
                <label>Marca:</label><br>
                <select name="marca" id="marcaSelect" onchange="buscarVolumes()" required style="padding:5px;width:200px;">
                    <option>Selecione uma marca</option>
                </select>
            </p>
            
            <p>
                <label>Volume da Embalagem:</label><br>
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
                <button type="reset" style="padding:8px 15px;background:gray;color:white;" onclick="limparSelects()">Fechar</button>
            </p>
        </form>
        <p><a href="/">🏠 Voltar</a></p>
    </div>
    
    <script>
    var reagentes = {reagentes_js};
    
    function limparSelects() {{
        document.getElementById('marcaSelect').innerHTML = '<option>Selecione uma marca</option>';
        document.getElementById('volumeSelect').innerHTML = '<option>Selecione um volume</option>';
    }}
    
    function buscarMarcas() {{
        var nome = document.getElementById('nomeReagente').value.toLowerCase();
        var marcaSelect = document.getElementById('marcaSelect');
        var volumeSelect = document.getElementById('volumeSelect');
        
        // Limpar selects
        marcaSelect.innerHTML = '<option>Selecione uma marca</option>';
        volumeSelect.innerHTML = '<option>Selecione um volume</option>';
        
        if (nome.length < 2) return;
        
        // Buscar marcas do reagente
        var marcasEncontradas = [];
        
        reagentes.forEach(function(r) {{
            if (r.nome.toLowerCase().includes(nome)) {{
                var marca = r.marca || 'Marca não informada';
                if (marcasEncontradas.indexOf(marca) === -1) {{
                    marcasEncontradas.push(marca);
                    var option = document.createElement('option');
                    option.value = marca;
                    option.text = marca;
                    marcaSelect.add(option);
                }}
            }}
        }});
    }}
    
    function buscarVolumes() {{
        var nome = document.getElementById('nomeReagente').value.toLowerCase();
        var marca = document.getElementById('marcaSelect').value;
        var volumeSelect = document.getElementById('volumeSelect');
        
        volumeSelect.innerHTML = '<option>Selecione um volume</option>';
        
        if (!nome || !marca || marca === 'Selecione uma marca') return;
        
        reagentes.forEach(function(r) {{
            if (r.nome.toLowerCase().includes(nome) && (r.marca || 'Marca não informada') === marca) {{
                var option = document.createElement('option');
                option.value = r.volume_nominal;
                option.text = r.volume_nominal + ' (' + r.quantidade_embalagens + ' disponíveis)';
                volumeSelect.add(option);
            }}
        }});
    }}
    </script>
    '''

@app.route('/entradas')
def entradas():
    if 'logged_in' not in session:
        return redirect('/login')
    
    html = '<h2>📦 Entradas de Reagentes</h2>'
    html += '<table border="1" style="width:100%;border-collapse:collapse;">'
    html += '<tr><th>Data</th><th>Reagente</th><th>Marca</th><th>Volume/Massa</th><th>Qtd Emb.</th><th>Localização</th><th>Controlado</th><th>Validade</th></tr>'
    
    for e in entradas_data:
        validade = e.get('data_validade', '') or 'N/A'
        controlado_cor = 'red' if e.get('controlado') == 'Sim' else 'green'
        html += f'<tr>'
        html += f'<td>{e["data_chegada"]}</td>'
        html += f'<td><b>{e["nome_reagente"]}</b></td>'
        html += f'<td>{e["marca"]}</td>'
        html += f'<td>{e["volume_nominal"]}</td>'
        html += f'<td><b>{e["quantidade_embalagens"]}</b></td>'
        html += f'<td>{e["localizacao"]}</td>'
        html += f'<td style="color:{controlado_cor}"><b>{e.get("controlado", "Não")}</b></td>'
        html += f'<td>{validade}</td>'
        html += f'</tr>'
    
    html += '</table>'
    html += '<p><a href="/entrada-reagente">➕ Nova Entrada</a></p>'
    html += '<p><a href="/">🏠 Voltar</a></p>'
    return html

@app.route('/saidas')
def saidas():
    if 'logged_in' not in session:
        return redirect('/login')
    
    html = '<h2>📤 Saídas de Reagentes</h2>'
    html += '<table border="1" style="width:100%;border-collapse:collapse;">'
    html += '<tr><th>Data</th><th>Reagente</th><th>Marca</th><th>Volume</th><th>Qtd Retirada</th><th>Usuário</th></tr>'
    
    for s in saidas_data:
        html += f'<tr>'
        html += f'<td>{s["data_saida"]}</td>'
        html += f'<td><b>{s["nome_reagente"]}</b></td>'
        html += f'<td>{s["marca"]}</td>'
        html += f'<td>{s["volume_nominal"]}</td>'
        html += f'<td><b style="color:red">{s["quantidade_saida"]} embalagens</b></td>'
        html += f'<td>{s["usuario"]}</td>'
        html += f'</tr>'
    
    html += '</table>'
    html += '<p><a href="/saida-reagente">➖ Nova Saída</a></p>'
    html += '<p><a href="/">🏠 Voltar</a></p>'
    return html

@app.route('/reagentes')
def reagentes():
    if 'logged_in' not in session:
        return redirect('/login')
    
    html = '<h2>🧪 Reagentes em Estoque</h2>'
    html += '<p><small>📦 <strong>Quantidade</strong> = Número total de embalagens</small></p>'
    html += '<table border="1" style="width:100%;border-collapse:collapse;">'
    html += '<tr><th>Nome do Reagente</th><th>Marca</th><th>Volume/Massa Nominal</th><th>Quantidade Total</th></tr>'
    
    for r in reagentes_data:
        volume = r.get('volume_nominal', 'N/A')
        marca = r.get('marca', 'N/A')
        html += f'<tr>'
        html += f'<td><b>{r["nome"]}</b></td>'
        html += f'<td>{marca}</td>'
        html += f'<td>{volume}</td>'
        html += f'<td><b>{r["quantidade_embalagens"]} embalagens</b></td>'
        html += f'</tr>'
    
    html += '</table>'
    html += '<p><small>💡 Reagentes são somados apenas se Nome + Marca + Volume forem iguais</small></p>'
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
        <p>Reagente: <b>{nome_reagente}</b></p>
        <p>Quantidade: <b>{quantidade_nominal}</b></p>
        <p>Data: {data_pedido}</p>
        <p>Controlado: {controlado}</p>
        <p><a href="/pedidos">📝 Ver Todos os Pedidos</a></p>
        <p><a href="/">🏠 Voltar ao Menu</a></p>
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
    html += '<tr><th>Reagente</th><th>Quantidade Nominal</th><th>Data</th><th>Controlado</th><th>Status</th></tr>'
    
    for p in pedidos_data:
        status_cor = 'green' if p['status'] == 'Finalizado' else 'orange'
        controlado_cor = 'red' if p['controlado'] == 'Sim' else 'green'
        html += f'<tr>'
        html += f'<td><b>{p["reagente"]}</b></td>'
        html += f'<td>{p["quantidade_nominal"]}</td>'
        html += f'<td>{p["data"]}</td>'
        html += f'<td style="color:{controlado_cor}"><b>{p["controlado"]}</b></td>'
        html += f'<td style="color:{status_cor}"><b>{p["status"]}</b></td>'
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
