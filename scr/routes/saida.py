from flask import Blueprint, jsonify, request, session
from src.models.user import User, db
from src.models.reagente import Reagente, Entrada, Saida
from src.routes.user import login_required
from datetime import datetime

saida_bp = Blueprint('saida', __name__)

@saida_bp.route('/saidas', methods=['GET'])
@login_required
def get_saidas():
    saidas = Saida.query.order_by(Saida.data_saida.desc()).all()
    return jsonify([saida.to_dict() for saida in saidas])

@saida_bp.route('/reagentes/buscar', methods=['GET'])
@login_required
def buscar_reagentes_para_saida():
    """Busca reagentes disponíveis para saída baseado no nome"""
    nome = request.args.get('nome', '').strip()
    
    if not nome:
        return jsonify({'error': 'Nome do reagente é obrigatório'}), 400
    
    # Buscar reagentes que contenham o nome
    reagentes = Reagente.query.filter(Reagente.nome.ilike(f'%{nome}%')).all()
    
    if not reagentes:
        return jsonify({'message': 'Nenhum reagente encontrado com esse nome'}), 404
    
    resultado = []
    for reagente in reagentes:
        # Buscar entradas disponíveis (com quantidade restante > 0)
        entradas_disponiveis = Entrada.query.filter(
            Entrada.reagente_id == reagente.id,
            Entrada.quantidade_restante > 0
        ).all()
        
        if entradas_disponiveis:
            for entrada in entradas_disponiveis:
                resultado.append({
                    'reagente_id': reagente.id,
                    'entrada_id': entrada.id,
                    'nome_reagente': reagente.nome,
                    'marca': entrada.marca,
                    'quantidade_nominal': entrada.quantidade_nominal,
                    'quantidade_restante': entrada.quantidade_restante,
                    'localizacao': entrada.localizacao,
                    'data_validade': entrada.data_validade.isoformat() if entrada.data_validade else None
                })
    
    if not resultado:
        return jsonify({'message': 'Reagente encontrado mas sem estoque disponível'}), 404
    
    return jsonify(resultado)

@saida_bp.route('/saidas', methods=['POST'])
@login_required
def create_saida():
    data = request.json
    
    # Validações
    required_fields = ['entrada_id', 'quantidade_abatida', 'data_saida']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} é obrigatório'}), 400
    
    try:
        data_saida = datetime.strptime(data['data_saida'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
    
    quantidade_abatida = float(data['quantidade_abatida'])
    if quantidade_abatida <= 0:
        return jsonify({'error': 'Quantidade deve ser maior que zero'}), 400
    
    # Buscar entrada
    entrada = Entrada.query.get_or_404(data['entrada_id'])
    
    # Verificar se há quantidade suficiente
    if quantidade_abatida > entrada.quantidade_restante:
        return jsonify({
            'error': f'Quantidade insuficiente. Disponível: {entrada.quantidade_restante}'
        }), 400
    
    # Criar saída
    saida = Saida(
        reagente_id=entrada.reagente_id,
        entrada_id=entrada.id,
        quantidade_abatida=quantidade_abatida,
        data_saida=data_saida,
        usuario_id=session['user_id'],
        observacoes=data.get('observacoes', '')
    )
    
    # Atualizar quantidade restante na entrada
    entrada.quantidade_restante -= quantidade_abatida
    
    # Atualizar quantidade total do reagente
    reagente = entrada.reagente
    reagente.quantidade_total -= quantidade_abatida
    
    db.session.add(saida)
    db.session.commit()
    
    return jsonify(saida.to_dict()), 201

@saida_bp.route('/saidas/<int:saida_id>', methods=['GET'])
@login_required
def get_saida(saida_id):
    saida = Saida.query.get_or_404(saida_id)
    return jsonify(saida.to_dict())

@saida_bp.route('/saidas/<int:saida_id>', methods=['PUT'])
@login_required
def update_saida(saida_id):
    saida = Saida.query.get_or_404(saida_id)
    data = request.json
    
    # Verificar se o usuário pode editar esta saída
    user = User.query.get(session['user_id'])
    if not user.is_admin() and saida.usuario_id != session['user_id']:
        return jsonify({'error': 'Você só pode editar suas próprias saídas'}), 403
    
    # Atualizar apenas campos permitidos (não quantidade)
    if data.get('data_saida'):
        try:
            saida.data_saida = datetime.strptime(data['data_saida'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
    
    saida.observacoes = data.get('observacoes', saida.observacoes)
    
    db.session.commit()
    return jsonify(saida.to_dict())

@saida_bp.route('/saidas/<int:saida_id>', methods=['DELETE'])
@login_required
def delete_saida(saida_id):
    saida = Saida.query.get_or_404(saida_id)
    
    # Verificar se o usuário pode deletar esta saída
    user = User.query.get(session['user_id'])
    if not user.is_admin() and saida.usuario_id != session['user_id']:
        return jsonify({'error': 'Você só pode deletar suas próprias saídas'}), 403
    
    # Reverter as quantidades
    entrada = saida.entrada
    entrada.quantidade_restante += saida.quantidade_abatida
    
    reagente = saida.reagente
    reagente.quantidade_total += saida.quantidade_abatida
    
    db.session.delete(saida)
    db.session.commit()
    return '', 204

