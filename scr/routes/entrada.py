from flask import Blueprint, jsonify, request, session
from src.models.user import User, db
from src.models.reagente import Pedido, Reagente, Entrada
from src.routes.user import login_required
from datetime import datetime

entrada_bp = Blueprint('entrada', __name__)

@entrada_bp.route('/entradas', methods=['GET'])
@login_required
def get_entradas():
    entradas = Entrada.query.order_by(Entrada.data_recebimento.desc()).all()
    return jsonify([entrada.to_dict() for entrada in entradas])

@entrada_bp.route('/entradas', methods=['POST'])
@login_required
def create_entrada():
    data = request.json
    
    # Validações básicas
    required_fields = ['quantidade_embalagens', 'data_recebimento', 'marca', 'localizacao', 'quantidade_nominal']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} é obrigatório'}), 400
    
    try:
        data_recebimento = datetime.strptime(data['data_recebimento'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Formato de data de recebimento inválido. Use YYYY-MM-DD'}), 400
    
    data_validade = None
    if data.get('data_validade'):
        try:
            data_validade = datetime.strptime(data['data_validade'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de data de validade inválido. Use YYYY-MM-DD'}), 400
    
    # Verificar se é um pedido preexistente
    pedido_id = data.get('pedido_id')
    reagente = None
    
    if pedido_id:
        # Entrada baseada em pedido existente
        pedido = Pedido.query.get_or_404(pedido_id)
        
        # Verificar se o pedido ainda está aberto
        if pedido.status == 'concluido':
            return jsonify({'error': 'Este pedido já foi concluído'}), 400
        
        # Buscar ou criar reagente baseado no pedido
        reagente = Reagente.query.filter_by(nome=pedido.nome_reagente).first()
        if not reagente:
            reagente = Reagente(
                nome=pedido.nome_reagente,
                controlado=pedido.controlado,
                quantidade_total=0.0
            )
            db.session.add(reagente)
            db.session.flush()  # Para obter o ID
        
        # Marcar pedido como concluído
        pedido.status = 'concluido'
        
    else:
        # Entrada sem pedido - todos os dados devem ser fornecidos
        nome_reagente = data.get('nome_reagente')
        if not nome_reagente:
            return jsonify({'error': 'nome_reagente é obrigatório quando não há pedido'}), 400
        
        controlado = data.get('controlado', False)
        
        # Buscar ou criar reagente
        reagente = Reagente.query.filter_by(nome=nome_reagente).first()
        if not reagente:
            reagente = Reagente(
                nome=nome_reagente,
                controlado=controlado,
                quantidade_total=0.0
            )
            db.session.add(reagente)
            db.session.flush()  # Para obter o ID
    
    # Calcular quantidade total baseada na quantidade nominal e número de embalagens
    try:
        # Extrair número da quantidade nominal (assumindo formato como "500ml", "1L", "250g", etc.)
        quantidade_str = data['quantidade_nominal']
        quantidade_numerica = float(''.join(filter(str.isdigit, quantidade_str.replace('.', '').replace(',', '.'))))
        quantidade_total_entrada = quantidade_numerica * data['quantidade_embalagens']
    except (ValueError, TypeError):
        return jsonify({'error': 'Formato de quantidade nominal inválido'}), 400
    
    # Criar entrada
    entrada = Entrada(
        reagente_id=reagente.id,
        pedido_id=pedido_id,
        quantidade_embalagens=data['quantidade_embalagens'],
        data_recebimento=data_recebimento,
        data_validade=data_validade,
        marca=data['marca'],
        localizacao=data['localizacao'],
        quantidade_nominal=data['quantidade_nominal'],
        quantidade_restante=quantidade_total_entrada,
        usuario_id=session['user_id']
    )
    
    # Atualizar quantidade total do reagente
    reagente.quantidade_total += quantidade_total_entrada
    
    db.session.add(entrada)
    db.session.commit()
    
    return jsonify(entrada.to_dict()), 201

@entrada_bp.route('/entradas/<int:entrada_id>', methods=['GET'])
@login_required
def get_entrada(entrada_id):
    entrada = Entrada.query.get_or_404(entrada_id)
    return jsonify(entrada.to_dict())

@entrada_bp.route('/entradas/<int:entrada_id>', methods=['PUT'])
@login_required
def update_entrada(entrada_id):
    entrada = Entrada.query.get_or_404(entrada_id)
    data = request.json
    
    # Verificar se o usuário pode editar esta entrada
    user = User.query.get(session['user_id'])
    if not user.is_admin() and entrada.usuario_id != session['user_id']:
        return jsonify({'error': 'Você só pode editar suas próprias entradas'}), 403
    
    # Atualizar campos permitidos
    if data.get('data_recebimento'):
        try:
            entrada.data_recebimento = datetime.strptime(data['data_recebimento'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de data de recebimento inválido. Use YYYY-MM-DD'}), 400
    
    if data.get('data_validade'):
        try:
            entrada.data_validade = datetime.strptime(data['data_validade'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de data de validade inválido. Use YYYY-MM-DD'}), 400
    
    entrada.marca = data.get('marca', entrada.marca)
    entrada.localizacao = data.get('localizacao', entrada.localizacao)
    
    db.session.commit()
    return jsonify(entrada.to_dict())

@entrada_bp.route('/entradas/<int:entrada_id>', methods=['DELETE'])
@login_required
def delete_entrada(entrada_id):
    entrada = Entrada.query.get_or_404(entrada_id)
    
    # Verificar se o usuário pode deletar esta entrada
    user = User.query.get(session['user_id'])
    if not user.is_admin() and entrada.usuario_id != session['user_id']:
        return jsonify({'error': 'Você só pode deletar suas próprias entradas'}), 403
    
    # Verificar se há saídas associadas
    if entrada.saidas:
        return jsonify({'error': 'Não é possível deletar entrada que possui saídas registradas'}), 400
    
    # Atualizar quantidade total do reagente
    reagente = entrada.reagente
    reagente.quantidade_total -= entrada.quantidade_restante
    
    # Se foi baseada em pedido, reabrir o pedido
    if entrada.pedido:
        entrada.pedido.status = 'aberto'
    
    db.session.delete(entrada)
    db.session.commit()
    return '', 204

