from flask import Blueprint, jsonify, request, session
from src.models.user import User, db
from src.models.reagente import Pedido, Reagente, Entrada, Saida
from src.routes.user import login_required

reagente_bp = Blueprint('reagente', __name__)

@reagente_bp.route('/reagentes/buscar', methods=['GET'])
@login_required
def buscar_reagentes():
    """Busca reagentes por nome e retorna todas as informações"""
    nome = request.args.get('nome', '').strip()
    
    if not nome:
        return jsonify({'error': 'Nome do reagente é obrigatório'}), 400
    
    # Buscar reagentes que contenham o nome
    reagentes = Reagente.query.filter(Reagente.nome.ilike(f'%{nome}%')).all()
    
    # Buscar também pedidos que contenham o nome (mesmo que não tenham chegado)
    pedidos_sem_entrada = Pedido.query.filter(
        Pedido.nome_reagente.ilike(f'%{nome}%'),
        Pedido.status == 'aberto'
    ).all()
    
    resultado = []
    
    # Adicionar reagentes em estoque
    for reagente in reagentes:
        entradas = Entrada.query.filter_by(reagente_id=reagente.id).all()
        
        for entrada in entradas:
            saidas = Saida.query.filter_by(entrada_id=entrada.id).all()
            historico_saidas = [saida.to_dict() for saida in saidas]
            
            item = {
                'tipo': 'estoque',
                'reagente_id': reagente.id,
                'nome': reagente.nome,
                'controlado': reagente.controlado,
                'quantidade_total_reagente': reagente.quantidade_total,
                'entrada': entrada.to_dict(),
                'historico_saidas': historico_saidas,
                'status': 'em_estoque'
            }
            resultado.append(item)
    
    # Adicionar pedidos sem entrada
    for pedido in pedidos_sem_entrada:
        item = {
            'tipo': 'pedido',
            'pedido_id': pedido.id,
            'nome': pedido.nome_reagente,
            'controlado': pedido.controlado,
            'quantidade_nominal': pedido.quantidade_nominal,
            'data_pedido': pedido.data_pedido.isoformat(),
            'status': 'nao_chegou'
        }
        resultado.append(item)
    
    if not resultado:
        return jsonify({'message': 'Nenhum reagente encontrado com esse nome'}), 404
    
    return jsonify(resultado)

@reagente_bp.route('/reagentes', methods=['GET'])
@login_required
def get_reagentes():
    """Lista todos os reagentes em estoque"""
    reagentes = Reagente.query.all()
    return jsonify([reagente.to_dict() for reagente in reagentes])

@reagente_bp.route('/relatorios/gerar', methods=['POST'])
@login_required
def gerar_relatorio():
    """Gera relatório em formato JSON (versão simplificada)"""
    data = request.json
    tipo_relatorio = data.get('tipo')
    
    tipos_validos = [
        'pedidos_abertos', 
        'pedidos_concluidos', 
        'estoque', 
        'historico_chegadas', 
        'historico_saidas'
    ]
    
    if tipo_relatorio not in tipos_validos:
        return jsonify({'error': 'Tipo de relatório inválido'}), 400
    
    try:
        # Gerar dados baseado no tipo
        if tipo_relatorio == 'pedidos_abertos':
            pedidos = Pedido.query.filter_by(status='aberto').order_by(Pedido.data_pedido.desc()).all()
            dados = [pedido.to_dict() for pedido in pedidos]
            
        elif tipo_relatorio == 'pedidos_concluidos':
            pedidos = Pedido.query.filter_by(status='concluido').order_by(Pedido.data_pedido.desc()).all()
            dados = [pedido.to_dict() for pedido in pedidos]
        
        elif tipo_relatorio == 'estoque':
            reagentes = Reagente.query.all()
            dados = [reagente.to_dict() for reagente in reagentes]
        
        elif tipo_relatorio == 'historico_chegadas':
            entradas = Entrada.query.order_by(Entrada.data_recebimento.desc()).all()
            dados = [entrada.to_dict() for entrada in entradas]
        
        elif tipo_relatorio == 'historico_saidas':
            saidas = Saida.query.order_by(Saida.data_saida.desc()).all()
            dados = [saida.to_dict() for saida in saidas]
        
        return jsonify({
            'tipo': tipo_relatorio,
            'dados': dados,
            'total': len(dados),
            'message': 'Relatório gerado com sucesso (formato JSON)'
        })
    
    except Exception as e:
        return jsonify({'error': f'Erro ao gerar relatório: {str(e)}'}), 500

