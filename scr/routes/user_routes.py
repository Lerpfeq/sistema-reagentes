from flask import Blueprint, request, session, redirect, url_for, jsonify, render_template_string
from functools import wraps
from src.models.user import User, db

user_bp = Blueprint('user', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        # Página de login simples
        return render_template_string('''
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
                            <small class="text-muted">Login inicial: admin / admin123</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
        ''')
    
    # POST - processar login
    username = request.form.get('username')
    password = request.form.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin()
        
        if user.is_admin():
            return redirect(url_for('user.dashboard_admin'))
        else:
            return redirect(url_for('user.dashboard_user'))
    else:
        return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Login - Erro</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container">
        <div class="row justify-content-center mt-5">
            <div class="col-md-6">
                <div class="alert alert-danger">❌ Usuário ou senha incorretos!</div>
                <a href="/login" class="btn btn-primary">Tentar novamente</a>
            </div>
        </div>
    </div>
</body>
</html>
        ''')

@user_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('user.login'))

@user_bp.route('/dashboard/admin')
@login_required
def dashboard_admin():
    user = User.query.get(session['user_id'])
    if not user.is_admin():
        return redirect(url_for('user.dashboard_user'))
    
    return render_template_string('''
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
                <span class="navbar-text me-3">Admin: {{username}}</span>
                <a class="nav-link" href="/logout">Sair</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h2>Dashboard Administrativo</h2>
                <div class="row mt-4">
                    <div class="col-md-3">
                        <div class="card bg-primary text-white">
                            <div class="card-body">
                                <h5>Pedidos</h5>
                                <p>Gerenciar pedidos de reagentes</p>
                                <a href="/api/pedidos" class="btn btn-light btn-sm">Ver Pedidos</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card bg-success text-white">
                            <div class="card-body">
                                <h5>Entradas</h5>
                                <p>Registrar chegada de reagentes</p>
                                <a href="/api/entradas" class="btn btn-light btn-sm">Ver Entradas</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card bg-warning text-white">
                            <div class="card-body">
                                <h5>Saídas</h5>
                                <p>Controlar uso de reagentes</p>
                                <a href="/api/saidas" class="btn btn-light btn-sm">Ver Saídas</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card bg-info text-white">
                            <div class="card-body">
                                <h5>Reagentes</h5>
                                <p>Buscar e gerenciar estoque</p>
                                <a href="/api/reagentes" class="btn btn-light btn-sm">Ver Reagentes</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    ''', username=session['username'])

@user_bp.route('/dashboard/user')
@login_required
def dashboard_user():
    return render_template_string('''
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
                <span class="navbar-text me-3">Usuário: {{username}}</span>
                <a class="nav-link" href="/logout">Sair</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h2>Dashboard do Usuário</h2>
                <div class="row mt-4">
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body">
                                <h5>Buscar Reagentes</h5>
                                <p>Consultar reagentes disponíveis</p>
                                <a href="/api/reagentes/buscar?nome=agua" class="btn btn-primary btn-sm">Buscar</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body">
                                <h5>Meus Pedidos</h5>
                                <p>Ver pedidos realizados</p>
                                <a href="/api/pedidos" class="btn btn-secondary btn-sm">Ver Pedidos</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body">
                                <h5>Relatórios</h5>
                                <p>Gerar relatórios</p>
                                <a href="/api/relatorios/gerar" class="btn btn-info btn-sm">Relatórios</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    ''', username=session['username'])