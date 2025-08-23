from src.models.user import db
from datetime import datetime

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_pedido = db.Column(db.Date, nullable=False)
    nome_reagente = db.Column(db.String(200), nullable=False)
    controlado = db.Column(db.Boolean, nullable=False, default=False)
    quantidade_nominal = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='aberto')  # 'aberto' ou 'concluido'
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relacionamentos
    entradas = db.relationship('Entrada', backref='pedido', lazy=True)

    def __repr__(self):
        return f'<Pedido {self.nome_reagente}>'

    def to_dict(self):
        return {
            'id': self.id,
            'data_pedido': self.data_pedido.isoformat() if self.data_pedido else None,
            'nome_reagente': self.nome_reagente,
            'controlado': self.controlado,
            'quantidade_nominal': self.quantidade_nominal,
            'status': self.status,
            'usuario_id': self.usuario_id,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None
        }

class Reagente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    controlado = db.Column(db.Boolean, nullable=False, default=False)
    quantidade_total = db.Column(db.Float, nullable=False, default=0.0)
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    entradas = db.relationship('Entrada', backref='reagente', lazy=True)
    saidas = db.relationship('Saida', backref='reagente', lazy=True)

    def __repr__(self):
        return f'<Reagente {self.nome}>'

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'controlado': self.controlado,
            'quantidade_total': self.quantidade_total,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }

class Entrada(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reagente_id = db.Column(db.Integer, db.ForeignKey('reagente.id'), nullable=False)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=True)
    quantidade_embalagens = db.Column(db.Integer, nullable=False)
    data_recebimento = db.Column(db.Date, nullable=False)
    data_validade = db.Column(db.Date, nullable=True)
    marca = db.Column(db.String(100), nullable=False)
    localizacao = db.Column(db.String(200), nullable=False)
    quantidade_nominal = db.Column(db.String(100), nullable=False)
    quantidade_restante = db.Column(db.Float, nullable=False)  # Para controle de saídas
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relacionamentos
    saidas = db.relationship('Saida', backref='entrada', lazy=True)

    def __repr__(self):
        return f'<Entrada {self.reagente.nome} - {self.marca}>'

    def to_dict(self):
        return {
            'id': self.id,
            'reagente_id': self.reagente_id,
            'pedido_id': self.pedido_id,
            'quantidade_embalagens': self.quantidade_embalagens,
            'data_recebimento': self.data_recebimento.isoformat() if self.data_recebimento else None,
            'data_validade': self.data_validade.isoformat() if self.data_validade else None,
            'marca': self.marca,
            'localizacao': self.localizacao,
            'quantidade_nominal': self.quantidade_nominal,
            'quantidade_restante': self.quantidade_restante,
            'usuario_id': self.usuario_id,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'reagente_nome': self.reagente.nome if self.reagente else None
        }

class Saida(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reagente_id = db.Column(db.Integer, db.ForeignKey('reagente.id'), nullable=False)
    entrada_id = db.Column(db.Integer, db.ForeignKey('entrada.id'), nullable=False)
    quantidade_abatida = db.Column(db.Float, nullable=False)
    data_saida = db.Column(db.Date, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    observacoes = db.Column(db.Text, nullable=True)
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Saida {self.reagente.nome} - {self.quantidade_abatida}>'

    def to_dict(self):
        return {
            'id': self.id,
            'reagente_id': self.reagente_id,
            'entrada_id': self.entrada_id,
            'quantidade_abatida': self.quantidade_abatida,
            'data_saida': self.data_saida.isoformat() if self.data_saida else None,
            'usuario_id': self.usuario_id,
            'observacoes': self.observacoes,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'reagente_nome': self.reagente.nome if self.reagente else None,
            'entrada_marca': self.entrada.marca if self.entrada else None
        }