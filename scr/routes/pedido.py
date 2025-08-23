from flask import Blueprint, jsonify, request, session
from src.models.user import User, db
from src.models.reagente import Pedido
from src.routes.user import login_required
from datetime import datetime

pedido_bp = Blueprint('pedido', __name__)

@pedido_bp.route('/pedidos', methods=['GET'])
@login_required
def get_pedidos():
    status = request.args.get('status')  # 'aberto', 'concluido', ou None para todos
    
    query = Pedido.query
    
    if status:
        query = query.filter_by(status=status)
    
    pedidos = query.order_by(Pedido.data_pedido.desc()).all()
    return jsonify([pedido.to_dict() for pedido in pedidos])

@pedido_bp.route('/pedidos', methods=['POST'])
@login_required
def create_pedido():
    data = request.json
    
    # Validações
    required_fields = ['data_pedido', 'nome_reagente', 'quantidade_nominal']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} é obrigatório'}), 400
    
    try:
        data_pedido = datetime.strptime(data['data_pedido'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
    
    pedido = Pedido(
        data_pedido=data_pedido,
        nome_reagente=data['nome_reagente'],
        controlado=data.get('controlado', False),
        quantidade_nominal=data['quantidade_nominal'],
        usuario_id=session['user_id']
    )
    
    db.session.add(pedido)
    db.session.commit()
    return jsonify(pedido.to_dict()), 201

@pedido_bp.route('/pedidos/<int:pedido_id>', methods=['GET'])
@login_required
def get_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    return jsonify(pedido.to_dict())

@pedido_bp.route('/pedidos/<int:pedido_id>', methods=['PUT'])
@login_required
def update_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    data = request.json
    
    # Verificar se o usuário pode editar este pedido
    user = User.query.get(session['user_id'])
    if not user.is_admin() and pedido.usuario_id != session['user_id']:
        return jsonify({'error': 'Você só pode editar seus próprios pedidos'}), 403
    
    # Não permitir edição se o pedido já foi concluído
    if pedido.status == 'concluido':
        return jsonify({'error': 'Não é possível editar pedidos concluídos'}), 400
    
    if data.get('data_pedido'):
        try:
            pedido.data_pedido = datetime.strptime(data['data_pedido'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
    
    pedido.nome_reagente = data.get('nome_reagente', pedido.nome_reagente)
    pedido.controlado = data.get('controlado', pedido.controlado)
    pedido.quantidade_nominal = data.get('quantidade_nominal', pedido.quantidade_nominal)
    
    db.session.commit()
    return jsonify(pedido.to_dict())

@pedido_bp.route('/pedidos/<int:pedido_id>', methods=['DELETE'])
@login_required
def delete_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    
    # Verificar se o usuário pode deletar este pedido
    user = User.query.get(session['user_id'])
    if not user.is_admin() and pedido.usuario_id != session['user_id']:
        return jsonify({'error': 'Você só pode deletar seus próprios pedidos'}), 403
    
    # Não permitir deleção se o pedido já foi concluído
    if pedido.status == 'concluido':
        return jsonify({'error': 'Não é possível deletar pedidos concluídos'}), 400
    
    db.session.delete(pedido)
    db.session.commit()
    return '', 204

@pedido_bp.route('/pedidos/abertos', methods=['GET'])
@login_required
def get_pedidos_abertos():
    """Retorna apenas pedidos em aberto para seleção na entrada de reagentes"""
    pedidos = Pedido.query.filter_by(status='aberto').order_by(Pedido.data_pedido.desc()).all()
    return jsonify([pedido.to_dict() for pedido in pedidos])

