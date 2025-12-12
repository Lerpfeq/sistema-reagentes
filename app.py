from flask import Flask, request, session, redirect
from datetime import datetime
import unicodedata

app = Flask(__name__)
app.secret_key = 'reagentes-secret-2024'

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def remover_acentos(texto):
    """
    Remove acentos de um texto.
    Exemplo: 'Ácido' -> 'Acido', 'São Paulo' -> 'Sao Paulo'
    """
    if not texto:
        return texto
    
    # Normaliza para NFD (decomposição)
    nfd = unicodedata.normalize('NFD', texto)
    # Remove caracteres de combinação (acentos)
    sem_acentos = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    return sem_acentos

def normalizar_para_comparacao(texto):
    """
    Prepara texto para comparação (remove acentos e converte para lowercase).
    """
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

def get_pedidos_abertos():
    return [p for p in pedidos_data if p['status'] == 'Aberto']

def finalizar_pedido(pedido_id):
    for p in pedidos_data:
        if p['id'] == pedido_id:
            p['status'] = 'Finalizado'
            break

def atualizar_reagente_quantidade(nome_reagente, volume_nominal, marca, quantidade_embalagens_adicionar, localizacao=''):
    """
    Atualiza quantidade de um reagente existente ou cria novo.
    Usa normalização de acentos para comparação.
    """
    # Normalizar para comparação
    nome_norm = normalizar_para_comparacao(nome_reagente)
    volume_norm = normalizar_para_comparacao(volume_nominal)
    marca_norm = normalizar_para_comparacao(marca)
    
    # Procura reagente existente
    for r in reagentes_data:
        if (normalizar_para_comparacao(r['nome']) == nome_norm and 
            normalizar_para_comparacao(r.get('volume_nominal', '')) == volume_norm and
            normalizar_para_comparacao(r.get('marca', '')) == marca_norm):
            r['quantidade_embalagens'] += quantidade_embalagens_adicionar
            if localizacao:
                r['localizacao'] = localizacao
            return
    
    # Se não existe, cria novo registro
    novo_id = max([r['id'] for r in reagentes_data]) + 1 if reagentes_data else 1
    reagentes_data.append({
        'id': novo_id,
        'nome': nome_reagente,
        'volume_nominal': volume_nominal,
        'marca': marca,
        'quantidade_embalagens': quantidade_embalagens_adicionar,
        'localizacao': localizacao or 'Não informada'
    })

# ============================================================================
# FUNÇÕES DE CONSULTA AVANÇADA
# ============================================================================

def consultar_reagentes(filtro_tipo='', filtro_valor=''):
    """
    Consulta reagentes com múltiplos filtros.
    Usa normalização de acentos para comparação.
    
    Tipos de filtro:
    - 'nome': busca por nome (contém)
    - 'marca': busca por marca exata
    - 'volume': busca por volume (contém)
    - 'localizacao': busca por localização
    - 'quantidade_min': quantidade mínima em estoque
    - 'quantidade_max': quantidade máxima em estoque
    - 'critico': mostra apenas reagentes com estoque crítico (< 5 embalagens)
    - 'zerado': mostra apenas reagentes zerados
    - 'todos': retorna todos
    
    Returns: lista de reagentes que atendem aos critérios
    """
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


def consultar_por_multiplos_filtros(nome=None, marca=None, volume=None, localizacao=None,
                                   estoque_min=None, estoque_max=None):
    """
    Consulta com múltiplos filtros simultâneos (AND logic).
    Usa normalização de acentos para comparação.
    
    Args:
        nome: substring do nome do reagente
        marca: marca exata (case-insensitive, sem acentos)
        volume: substring do volume/massa
        localizacao: substring da localização
        estoque_min: quantidade mínima de embalagens
        estoque_max: quantidade máxima de embalagens
    
    Returns: lista de reagentes que atendem a TODOS os critérios
    """
    resultados = reagentes_data
    
    if nome:
        nome_norm = normalizar_para_comparacao(nome)
        resultados = [r for r in resultados 
                     if nome_norm in normalizar_para_comparacao(r['nome'])]
    
    if marca:
        marca_norm = normalizar_para_comparacao(marca)
        resultados = [r for r in resultados 
                     if normalizar_para_comparacao(r.get('marca', '')) == marca_norm]
    
    if volume:
        volume_norm = normalizar_para_comparacao(volume)
        resultados = [r for r in resultados 
                     if volume_norm in normalizar_para_comparacao(r.get('volume_nominal', ''))]
    
    if localizacao:
        localizacao_norm = normalizar_para_comparacao(localizacao)
        resultados = [r for r in resultados 
                     if localizacao_norm in normalizar_para_comparacao(r.get('localizacao', ''))]
    
    if estoque_min is not None:
        try:
            min_val = int(estoque_min)
            resultados = [r for r in resultados 
                         if r['quantidade_embalagens'] >= min_val]
        except (ValueError, TypeError):
            pass
    
    if estoque_max is not None:
        try:
            max_val = int(estoque_max)
            resultados = [r for r in resultados 
                         if r['quantidade_embalagens'] <= max_val]
        except (ValueError, TypeError):
            pass
    
    return resultados


def gerar_relatorio_estoque():
    """Gera um relatório completo do estoque com estatísticas."""
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


def consultar_entradas_por_periodo(data_inicio, data_fim):
    """Consulta entradas de reagentes em um período específico."""
    try:
        inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        fim = datetime.strptime(data_fim, '%Y-%m-%d')
    except ValueError:
        return []
    
    resultados = []
    for e in entradas_data:
        try:
            data_entrada = datetime.strptime(e['data_chegada'], '%Y-%m-%d')
            if inicio <= data_entrada <= fim:
                resultados.append(e)
        except ValueError:
            pass
    
    return resultados


def consultar_saidas_por_reagente(nome_reagente):
    """Retorna todas as saídas de um reagente específico (ignora acentos)."""
    nome_norm = normalizar_para_comparacao(nome_reagente)
    return [s for s in saidas_data 
            if normalizar_para_comparacao(s['nome_reagente']) == nome_norm]


def consultar_estoque_por_marca():
    """Retorna um dicionário agrupando reagentes por marca."""
    por_marca = {}
    
    for r in reagentes_data:
        marca = r.get('marca', 'Sem marca informada')
        if marca not in por_marca:
            por_marca[marca] = []
        por_marca[marca].append(r)
    
    return por_marca


def consultar_estoque_por_localizacao():
    """Retorna um dicionário agrupando reagentes por localização."""
    por_localizacao = {}
    
    for r in reagentes_data:
        localizacao = r.get('localizacao', 'Não informada')
        if localizacao not in por_localizacao:
            por_localizacao[localizacao] = []
        por_localizacao[localizacao].append(r)
    
    return por_localizacao


def consultar_pedidos(status='todos'):
    """
    Consulta pedidos por status.
    
    Args:
        status: 'abertos', 'recebidos' ou 'todos'
    
    Returns: lista de pedidos filtrada
    """
    if status == 'abertos':
        return [p for p in pedidos_data if p['status'] == 'Aberto']
    elif status == 'recebidos':
        return [p for p in pedidos_data if p['status'] == 'Finalizado']
    else:
        return pedidos_data


def gerar_relatorio_pedidos():
    """Gera um relatório completo de pedidos."""
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

# ============================================================================
# ROTAS
# ============================================================================

@app.route('/')
def home():
    if 'logged_in' not in session:
        return redirect('/login')
    
    return '''
    <h1>🧪 Sistema de Reagentes</h1>
    <p>✅ Logado como: admin</p>
    <p><a href="/reagentes">📋 Ver Reagentes</a></p>
    <p><a href="/consulta">🔍 Consultar Reagentes</a></p>
    <p><a href="/relatorio">📊 Relatório de Estoque</a></p>
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
        
        # Atualizar quantidade do reagente (com normalização de acentos)
        atualizar_reagente_quantidade(nome_reagente, volume_nominal, marca, quantidade_embalagens, localizacao)
        
        return f'''
        <h2>✅ Entrada Registrada!</h2>
        <p>Reagente: <b>{nome_reagente}</b> ({volume_nominal})</p>
        <p>Marca: <b>{marca}</b></p>
        <p>Quantidade: <b>{quantidade_embalagens} embalagens</b></p>
        <p>Localização: <b>{localizacao}</b></p>
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
                <br><small style="color:blue;">💡 Reagentes só somam se Nome + Volume + Marca forem iguais (acentos não importam)</small>
            </p>
            
            <p>
                <label>Quantidade de Embalagens:</label><br>
                <input type="number" name="quantidade_embalagens" min="1" required style="width:100px;padding:5px;">
            </p>
            
            <p>
                <label>📍 Localização:</label><br>
                <input type="text" name="localizacao" placeholder="Ex: Prateleira A1, Armário C3" required style="width:300px;padding:5px;">
                <br><small style="color:green;">✓ Campo obrigatório para localizar o reagente</small>
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
        
        # Normalizar para busca (ignora acentos)
        nome_norm = normalizar_para_comparacao(nome_reagente)
        marca_norm = normalizar_para_comparacao(marca)
        volume_norm = normalizar_para_comparacao(volume_nominal)
        
        # Buscar reagente específico
        reagente_encontrado = None
        for r in reagentes_data:
            if (normalizar_para_comparacao(r['nome']) == nome_norm and 
                normalizar_para_comparacao(r.get('marca', '')) == marca_norm and
                normalizar_para_comparacao(r.get('volume_nominal', '')) == volume_norm):
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
            localizacao = reagente_encontrado.get('localizacao', 'Não informada')
            return f'''
            <h2>❌ Quantidade Insuficiente!</h2>
            <p>Reagente: <b>{reagente_encontrado['nome']}</b></p>
            <p>Marca: <b>{reagente_encontrado.get('marca', 'N/A')}</b> - Volume: <b>{reagente_encontrado.get('volume_nominal', 'N/A')}</b></p>
            <p>Localização: <b>{localizacao}</b></p>
            <p>Disponível: <b>{reagente_encontrado['quantidade_embalagens']} embalagens</b></p>
            <p>Solicitado: <b>{quantidade_saida} embalagens</b></p>
            <p><a href="/saida-reagente">Tentar novamente</a></p>
            <p><a href="/">Voltar ao Menu</a></p>
            '''
        
        # Registrar saída
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
        <p>Reagente: <b>{reagente_encontrado['nome']}</b></p>
        <p>Marca: <b>{reagente_encontrado.get('marca', 'N/A')}</b></p>
        <p>Volume: <b>{reagente_encontrado.get('volume_nominal', 'N/A')}</b></p>
        <p>Localização: <b>{reagente_encontrado.get('localizacao', 'N/A')}</b></p>
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
                option.text = r.volume_nominal + ' (' + r.quantidade_embalagens + ' disponíveis) - ' + r.localizacao;
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
    html += '<tr><th>Data</th><th>Reagente</th><th>Marca</th><th>Volume/Massa</th><th>Qtd Emb.</th><th>📍 Localização</th><th>Controlado</th><th>Validade</th></tr>'
    
    for e in entradas_data:
        validade = e.get('data_validade', '') or 'N/A'
        controlado_cor = 'red' if e.get('controlado') == 'Sim' else 'green'
        html += f'<tr>'
        html += f'<td>{e["data_chegada"]}</td>'
        html += f'<td><b>{e["nome_reagente"]}</b></td>'
        html += f'<td>{e["marca"]}</td>'
        html += f'<td>{e["volume_nominal"]}</td>'
        html += f'<td><b>{e["quantidade_embalagens"]}</b></td>'
        html += f'<td><b>{e.get("localizacao", "N/A")}</b></td>'
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
    html += '<tr><th>Data</th><th>Reagente</th><th>Marca</th><th>Volume</th><th>📍 Localização</th><th>Qtd Retirada</th><th>Usuário</th></tr>'
    
    for s in saidas_data:
        html += f'<tr>'
        html += f'<td>{s["data_saida"]}</td>'
        html += f'<td><b>{s["nome_reagente"]}</b></td>'
        html += f'<td>{s["marca"]}</td>'
        html += f'<td>{s["volume_nominal"]}</td>'
        html += f'<td><b>{s.get("localizacao", "N/A")}</b></td>'
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
    html += '<tr><th>Nome do Reagente</th><th>Marca</th><th>Volume/Massa Nominal</th><th>📍 Localização</th><th>Quantidade Total</th></tr>'
    
    for r in reagentes_data:
        volume = r.get('volume_nominal', 'N/A')
        marca = r.get('marca', 'N/A')
        localizacao = r.get('localizacao', 'Não informada')
        html += f'<tr>'
        html += f'<td><b>{r["nome"]}</b></td>'
        html += f'<td>{marca}</td>'
        html += f'<td>{volume}</td>'
        html += f'<td><b>{localizacao}</b></td>'
        html += f'<td><b>{r["quantidade_embalagens"]} embalagens</b></td>'
        html += f'</tr>'
    
    html += '</table>'
    html += '<p><small>💡 Reagentes são somados apenas se Nome + Marca + Volume forem iguais (acentos não importam)</small></p>'
    html += '<p><a href="/">🏠 Voltar</a></p>'
    return html

@app.route('/consulta', methods=['GET', 'POST'])
def consulta():
    """Página de consulta com abas: Reagentes, Pedidos Abertos e Pedidos Recebidos."""
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
    
    # Dados para as abas
    pedidos_abertos = consultar_pedidos('abertos')
    pedidos_recebidos = consultar_pedidos('recebidos')
    
    # HTML para ABA REAGENTES
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
    
    # HTML para ABA PEDIDOS ABERTOS
    html_abertos = '<table border="1" style="width:100%;border-collapse:collapse;">'
    html_abertos += '<tr style="background-color:#fff3cd;"><th>Reagente</th><th>Quantidade</th><th>Data</th><th>Controlado</th><th>Status</th></tr>'
    
    if pedidos_abertos:
        for p in pedidos_abertos:
            controlado_cor = 'red' if p['controlado'] == 'Sim' else 'green'
            html_abertos += f'<tr style="background-color:#fffacd;"><td><b>{p["reagente"]}</b></td><td>{p["quantidade_nominal"]}</td><td>{p["data"]}</td><td style="color:{controlado_cor};"><b>{p["controlado"]}</b></td><td style="color:orange;"><b>⏳ {p["status"]}</b></td></tr>'
    else:
        html_abertos += '<tr><td colspan="5" style="text-align:center;color:green;">✅ Nenhum pedido aberto</td></tr>'
    
    html_abertos += '</table>'
    
    # HTML para ABA PEDIDOS RECEBIDOS
    html_recebidos = '<table border="1" style="width:100%;border-collapse:collapse;">'
    html_recebidos += '<tr style="background-color:#d4edda;"><th>Reagente</th><th>Quantidade</th><th>Data</th><th>Controlado</th><th>Status</th></tr>'
    
    if pedidos_recebidos:
        for p in pedidos_recebidos:
            controlado_cor = 'red' if p['controlado'] == 'Sim' else 'green'
            html_recebidos += f'<tr style="background-color:#e8f5e9;"><td><b>{p["reagente"]}</b></td><td>{p["quantidade_nominal"]}</td><td>{p["data"]}</td><td style="color:{controlado_cor};"><b>{p["controlado"]}</b></td><td style="color:green;"><b>✅ {p["status"]}</b></td></tr>'
    else:
        html_recebidos += '<tr><td colspan="5" style="text-align:center;color:gray;">Nenhum pedido recebido ainda</td></tr>'
    
    html_recebidos += '</table>'
    
    # CSS para abas
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
                <small style="display:block;margin-top:5px;color:blue;">💡 Para 'Estoque Crítico' e 'Zerado', deixe este campo vazio</small>
                <small style="display:block;margin-top:5px;color:green;">✓ Acentos não importam (Ácido = Acido)</small>
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

@app.route('/relatorio')
def relatorio():
    """Exibe relatório de estoque com estatísticas, localização e pedidos."""
    if 'logged_in' not in session:
        return redirect('/login')
    
    relatorio_estoque = gerar_relatorio_estoque()
    relatorio_pedidos = gerar_relatorio_pedidos()
    por_localizacao = consultar_estoque_por_localizacao()
    
    # Itens críticos
    html_criticos = '<tr><td colspan="5" style="text-align:center;color:green;">✅ Nenhum item crítico</td></tr>'
    if relatorio_estoque['itens_criticos']:
        html_criticos = ''
        for r in relatorio_estoque['itens_criticos']:
            html_criticos += f'<tr style="background-color:#ffe6e6;"><td><b>{r["nome"]}</b></td><td>{r.get("marca", "N/A")}</td><td>{r.get("volume_nominal", "N/A")}</td><td><b>{r.get("localizacao", "N/A")}</b></td><td style="color:red;"><b>{r["quantidade_embalagens"]}</b></td></tr>'
    
    # Itens zerados
    html_zerados = '<tr><td colspan="5" style="text-align:center;color:green;">✅ Nenhum item zerado</td></tr>'
    if relatorio_estoque['itens_zerados']:
        html_zerados = ''
        for r in relatorio_estoque['itens_zerados']:
            html_zerados += f'<tr style="background-color:#ffcccc;"><td><b>{r["nome"]}</b></td><td>{r.get("marca", "N/A")}</td><td>{r.get("volume_nominal", "N/A")}</td><td><b>{r.get("localizacao", "N/A")}</b></td><td style="color:darkred;"><b>0</b></td></tr>'
    
    # Pedidos abertos
    html_pedidos_abertos = '<tr><td colspan="5" style="text-align:center;color:green;">✅ Nenhum pedido aberto</td></tr>'
    if relatorio_pedidos['pedidos_abertos']:
        html_pedidos_abertos = ''
        for p in relatorio_pedidos['pedidos_abertos']:
            controlado_cor = 'red' if p['controlado'] == 'Sim' else 'green'
            html_pedidos_abertos += f'<tr style="background-color:#fffacd;"><td><b>{p["reagente"]}</b></td><td>{p["quantidade_nominal"]}</td><td>{p["data"]}</td><td style="color:{controlado_cor};"><b>{p["controlado"]}</b></td><td style="color:orange;"><b>⏳ {p["status"]}</b></td></tr>'
    
    # Pedidos recebidos
    html_pedidos_recebidos = '<tr><td colspan="5" style="text-align:center;color:gray;">Nenhum pedido recebido ainda</td></tr>'
    if relatorio_pedidos['pedidos_recebidos']:
        html_pedidos_recebidos = ''
        for p in relatorio_pedidos['pedidos_recebidos']:
            controlado_cor = 'red' if p['controlado'] == 'Sim' else 'green'
            html_pedidos_recebidos += f'<tr style="background-color:#e8f5e9;"><td><b>{p["reagente"]}</b></td><td>{p["quantidade_nominal"]}</td><td>{p["data"]}</td><td style="color:{controlado_cor};"><b>{p["controlado"]}</b></td><td style="color:green;"><b>✅ {p["status"]}</b></td></tr>'
    
    # Reagentes por localização
    html_por_localizacao = ''
    for localizacao, reagentes in sorted(por_localizacao.items()):
        total_qtd = sum(r['quantidade_embalagens'] for r in reagentes)
        html_por_localizacao += f'<h4>📍 {localizacao} ({len(reagentes)} itens)</h4>'
        html_por_localizacao += '<table border="1" style="width:100%;border-collapse:collapse;margin-bottom:10px;">'
        html_por_localizacao += '<tr><th>Reagente</th><th>Marca</th><th>Volume</th><th>Quantidade</th></tr>'
        for r in reagentes:
            html_por_localizacao += f'<tr><td>{r["nome"]}</td><td>{r.get("marca", "N/A")}</td><td>{r.get("volume_nominal", "N/A")}</td><td><b>{r["quantidade_embalagens"]}</b></td></tr>'
        html_por_localizacao += '</table>'
    
    item_maior = relatorio_estoque['item_com_maior_estoque']
    maior_nome = f"{item_maior['nome']} ({item_maior.get('localizacao', 'N/A')}) - {item_maior['quantidade_embalagens']} unidades" if item_maior else "N/A"
    
    return f'''
    <div style="margin:20px;padding:20px;">
        <h2>📊 Relatório Completo</h2>
        
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;margin-bottom:30px;">
            <div style="border:1px solid #ddd;padding:15px;border-radius:5px;background:#f0f7ff;">
                <h3 style="margin:0;">📦 Total de Itens</h3>
                <p style="font-size:24px;color:blue;font-weight:bold;margin:10px 0;">{relatorio_estoque["total_itens"]}</p>
            </div>
            
            <div style="border:1px solid #ddd;padding:15px;border-radius:5px;background:#f0fff4;">
                <h3 style="margin:0;">📊 Total de Embalagens</h3>
                <p style="font-size:24px;color:green;font-weight:bold;margin:10px 0;">{relatorio_estoque["total_embalagens"]}</p>
            </div>
            
            <div style="border:1px solid #ddd;padding:15px;border-radius:5px;background:#faf5ff;">
                <h3 style="margin:0;">📈 Média de Estoque</h3>
                <p style="font-size:24px;color:purple;font-weight:bold;margin:10px 0;">{relatorio_estoque["media_embalagens"]}</p>
            </div>
        </div>
        
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:30px;">
            <div style="border:1px solid #ff9800;padding:15px;border-radius:5px;background:#fff3e0;">
                <h3 style="margin:0;">⏳ Pedidos Abertos</h3>
                <p style="font-size:24px;color:#ff9800;font-weight:bold;margin:10px 0;">{relatorio_pedidos["total_abertos"]}</p>
            </div>
            
            <div style="border:1px solid #4caf50;padding:15px;border-radius:5px;background:#f1f8e9;">
                <h3 style="margin:0;">✅ Pedidos Recebidos</h3>
                <p style="font-size:24px;color:#4caf50;font-weight:bold;margin:10px 0;">{relatorio_pedidos["total_recebidos"]}</p>
            </div>
        </div>
        
        <h3>⚠️ Itens com Estoque Crítico (&lt; 5)</h3>
        <table border="1" style="width:100%;border-collapse:collapse;margin-bottom:20px;">
            <tr style="background-color:#ffcccc;"><th>Nome</th><th>Marca</th><th>Volume</th><th>📍 Localização</th><th>Quantidade</th></tr>
            {html_criticos}
        </table>
        
        <h3>❌ Itens com Estoque Zerado</h3>
        <table border="1" style="width:100%;border-collapse:collapse;margin-bottom:20px;">
            <tr style="background-color:#ffcccc;"><th>Nome</th><th>Marca</th><th>Volume</th><th>📍 Localização</th><th>Quantidade</th></tr>
            {html_zerados}
        </table>
        
        <h3>⏳ Pedidos Abertos ({relatorio_pedidos["total_abertos"]})</h3>
        <table border="1" style="width:100%;border-collapse:collapse;margin-bottom:20px;">
            <tr style="background-color:#fff3cd;"><th>Reagente</th><th>Quantidade</th><th>Data</th><th>Controlado</th><th>Status</th></tr>
            {html_pedidos_abertos}
        </table>
        
        <h3>✅ Pedidos Recebidos ({relatorio_pedidos["total_recebidos"]})</h3>
        <table border="1" style="width:100%;border-collapse:collapse;margin-bottom:20px;">
            <tr style="background-color:#d4edda;"><th>Reagente</th><th>Quantidade</th><th>Data</th><th>Controlado</th><th>Status</th></tr>
            {html_pedidos_recebidos}
        </table>
        
        <div style="background:#e6f2ff;padding:15px;border-radius:5px;margin-top:20px;margin-bottom:20px;">
            <h3 style="margin-top:0;">🏆 Item com Maior Estoque</h3>
            <p style="font-size:16px;">{maior_nome}</p>
        </div>
        
        <h3>📍 Reagentes por Localização</h3>
        {html_por_localizacao}
        
        <p><a href="/">🏠 Voltar ao Menu</a></p>
    </div>
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
            <div style="max-width:400px;margin:50px auto;padding:20px;border:1px solid #ccc;border-radius:5px;">
                <form method="post">
                    <h2>🔐 Login Sistema</h2>
                    <p style="color:red;font-weight:bold;">{erro}</p>
                    <p>Usuário: <input name="username" required style="width:100%;padding:8px;box-sizing:border-box;"></p>
                    <p>Senha: <input type="password" name="password" required style="width:100%;padding:8px;box-sizing:border-box;"></p>
                    <button style="width:100%;padding:10px;background:blue;color:white;border:none;border-radius:5px;cursor:pointer;font-weight:bold;">Entrar</button>
                </form>
                <p style="text-align:center;margin-top:15px;"><small>Use: <b>admin</b> / <b>admin123</b></small></p>
            </div>
            '''
    
    return '''
    <div style="max-width:400px;margin:50px auto;padding:20px;border:1px solid #ccc;border-radius:5px;box-shadow:0 2px 5px rgba(0,0,0,0.1);">
        <form method="post">
            <h2 style="text-align:center;">🔐 Login Sistema de Reagentes</h2>
            <p>
                <label style="font-weight:bold;">Usuário:</label><br>
                <input name="username" required style="width:100%;padding:8px;box-sizing:border-box;border:1px solid #ddd;border-radius:3px;margin-top:5px;">
            </p>
            <p>
                <label style="font-weight:bold;">Senha:</label><br>
                <input type="password" name="password" required style="width:100%;padding:8px;box-sizing:border-box;border:1px solid #ddd;border-radius:3px;margin-top:5px;">
            </p>
            <button style="width:100%;padding:10px;background:blue;color:white;border:none;border-radius:5px;cursor:pointer;font-weight:bold;font-size:16px;">Entrar</button>
        </form>
        <p style="text-align:center;margin-top:20px;color:#666;"><small>Credenciais de teste:</small></p>
        <p style="text-align:center;background:#f0f0f0;padding:10px;border-radius:3px;font-family:monospace;">
            👤 <b>admin</b><br>
            🔑 <b>admin123</b>
        </p>
    </div>
    '''

@app.route('/logout')
def logout():
    """Logout do sistema."""
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
