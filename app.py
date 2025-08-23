import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template_string, session, redirect, url_for, request, jsonify, flash
from src.models.user import db, User, Reagente, Pedido, Entrada, Saida
from datetime import datetime, date
from functools import wraps

def create_app():
    app = Flask(__name__)
    
    # Configuração SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reagentes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'reagentes-lab-secret-key-2024')
    
    # Inicializar banco
    db.init_app(app)
    
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function

    # ROTAS DE AUTENTICAÇÃO
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                session['user_id'] = user.id
                session['username'] = user.username
                session['is_admin'] = user.is_admin()
                
                if user.is_admin():
                    return redirect(url_for('dashboard_admin'))
                else:
                    return redirect(url_for('dashboard_user'))
            else:
                return render_template_string(LOGIN_TEMPLATE, error="Usuário ou senha incorretos!")
        
        return render_template_string(LOGIN_TEMPLATE)

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    # ROTAS PRINCIPAIS
    @app.route('/')
    def index():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        user = User.query.get(session['user_id'])
        if user and user.is_admin():
            return redirect(url_for('dashboard_admin'))
        else:
            return redirect(url_for('dashboard_user'))

    @app.route('/dashboard/admin')
    @login_required
    def dashboard_admin():
        user = User.query.get(session['user_id'])
        if not user.is_admin():
            return redirect(url_for('dashboard_user'))
        
        # Estatísticas
        total_pedidos = Pedido.query.count()
        pedidos_abertos = Pedido.query.filter_by(status='aberto').count()
        total_reagentes = Reagente.query.count()
        total_entradas = Entrada.query.count()
        
        return render_template_string(ADMIN_DASHBOARD_TEMPLATE, 
            username=session['username'],
            total_pedidos=total_pedidos,
            pedidos_abertos=pedidos_abertos,
            total_reagentes=total_reagentes,
            total_entradas=total_entradas
        )

    @app.route('/dashboard/user')
    @login_required
    def dashboard_user():
        # Pedidos do usuário
        meus_pedidos = Pedido.query.filter_by(usuario_id=session['user_id']).count()
        pedidos_abertos = Pedido.query.filter_by(usuario_id=session['user_id'], status='aberto').count()
        
        return render_template_string(USER_DASHBOARD_TEMPLATE,
            username=session['username'],
            meus_pedidos=meus_pedidos,
            pedidos_abertos=pedidos_abertos
        )

    # API ROUTES
    @app.route('/api/pedidos', methods=['GET', 'POST'])
    @login_required
    def pedidos():
        if request.method == 'POST':
            data = request.json
            pedido = Pedido(
                data_pedido=datetime.strptime(data['data_pedido'], '%Y-%m-%d').date(),
                nome_reagente=data['nome_reagente'],
                controlado=data.get('controlado', False),
                quantidade_nominal=data['quantidade_nominal'],
                usuario_id=session['user_id']
            )
            db.session.add(pedido)
            db.session.commit()
            return jsonify(pedido.to_dict()), 201
        
        pedidos = Pedido.query.order_by(Pedido.data_pedido.desc()).all()
        return jsonify([p.to_dict() for p in pedidos])

    @app.route('/api/reagentes')
    @login_required
    def reagentes():
        reagentes = Reagente.query.all()
        return jsonify([r.to_dict() for r in reagentes])

    @app.route('/api/reagentes/buscar')
    @login_required
    def buscar_reagentes():
        nome = request.args.get('nome', '').strip()
        if not nome:
            return jsonify({'error': 'Nome é obrigatório'}), 400
            
        reagentes = Reagente.query.filter(Reagente.nome.ilike(f'%{nome}%')).all()
        
        resultado = []
        for reagente in reagentes:
            entradas = Entrada.query.filter_by(reagente_id=reagente.id).all()
            for entrada in entradas:
                resultado.append({
                    'reagente_id': reagente.id,
                    'nome': reagente.nome,
                    'entrada': entrada.to_dict()
                })
        
        return jsonify(resultado)

    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Sistema de Reagentes Online - SQLite!'}, 200

    # Criar tabelas e dados iniciais
    with app.app_context():
        db.create_all()
        
        # Criar usuário admin
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@reagentes.com',
                tipo='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin criado: admin / admin123")
            
        # Criar usuário comum
        user = User.query.filter_by(username='user').first()
        if not user:
            user = User(
                username='user',
                email='user@reagentes.com',
                tipo='usuario'
            )
            user.set_password('user123')
            db.session.add(user)
            db.session.commit()
            print("✅ Usuário criado: user / user123")
    
    return app

# TEMPLATES HTML
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Sistema de Reagentes - Login</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container">
        <div class="row justify-content-center mt-5">
            <div class="col-md-6">
                <div class="card shadow">
                    <div class="card-body">
                        <h3 class="card-title text-center mb-4">🧪 Sistema de Reagentes</h3>
                        {% if error %}
                        <div class="alert alert-danger">❌ {{ error }}</div>
                        {% endif %}
                        <form method="POST">
                            <div class="mb-3">
                                <label class="form-label">Usuário</label>
                                <input type="text" class="form-control" name="username" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Senha</label>
                                <input type="password" class="form-control" name="password" required>
                            </div>
                            <div class="d-grid">
                                <button type="submit" class="btn btn-primary">Entrar</button>
                            </div>
                        </form>
                        <div class="text-center mt-3">
                            <small class="text-muted">
                                Admin: admin/admin123<br>
                                Usuário: user/user123
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

ADMIN_DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard Admin</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="#">🧪 Sistema de Reagentes</a>
            <div class="navbar-nav ms-auto">
                <span class="navbar-text me-3">Admin: {{ username }}</span>
                <a class="nav-link" href="/logout">Sair</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        <h2>Dashboard Administrativo</h2>
        
        <div class="row mt-4">
            <div class="col-md-3">
                <div class="card bg-primary text-white">
                    <div class="card-body">
                        <h5>📝 Pedidos</h5>
                        <h3>{{ total_pedidos }}</h3>
                        <small>Total de pedidos</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-warning text-white">
                    <div class="card-body">
                        <h5>⏳ Abertos</h5>
                        <h3>{{ pedidos_abertos }}</h3>
                        <small>Pedidos pendentes</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-success text-white">
                    <div class="card-body">
                        <h5>🧪 Reagentes</h5>
                        <h3>{{ total_reagentes }}</h3>
                        <small>Em estoque</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-info text-white">
                    <div class="card-body">
                        <h5>📦 Entradas</h5>
                        <h3>{{ total_entradas }}</h3>
                        <small>Registradas</small>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-12">
                <h4>🔗 APIs Disponíveis</h4>
                <div class="list-group">
                    <a href="/api/pedidos" class="list-group-item">📝 /api/pedidos - Ver todos os pedidos</a>
                    <a href="/api/reagentes" class="list-group-item">🧪 /api/reagentes - Ver reagentes</a>
                    <a href="/api/reagentes/buscar?nome=agua" class="list-group-item">🔍 /api/reagentes/buscar?nome=agua - Buscar reagente</a>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

USER_DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard Usuário</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-secondary">
        <div class="container">
            <a class="navbar-brand" href="#">🧪 Sistema de Reagentes</a>
            <div class="navbar-nav ms-auto">
                <span class="navbar-text me-3">Usuário: {{ username }}</span>
                <a class="nav-link" href="/logout">Sair</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        <h2>Dashboard do Usuário</h2>
        
        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card bg-primary text-white">
                    <div class="card-body">
                        <h5>📝 Meus Pedidos</h5>
                        <h3>{{ meus_pedidos }}</h3>
                        <small>Total de pedidos feitos</small>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card bg-warning text-white">
                    <div class="card-body">
                        <h5>⏳ Pendentes</h5>
                        <h3>{{ pedidos_abertos }}</h3>
                        <small>Aguardando chegada</small>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-12">
                <h4>🔗 Funcionalidades</h4>
                <div class="list-group">
                    <a href="/api/reagentes/buscar?nome=agua" class="list-group-item">🔍 Buscar reagentes</a>
                    <a href="/api/pedidos" class="list-group-item">📝 Ver meus pedidos</a>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
