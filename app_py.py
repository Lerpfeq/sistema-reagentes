import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, session, redirect, url_for
from src.models.user import db, User
from src.routes.user import user_bp
from src.routes.pedido import pedido_bp
from src.routes.entrada import entrada_bp
from src.routes.saida import saida_bp
from src.routes.reagente_simple import reagente_bp

def create_app():
    app = Flask(__name__)
    
    # Configuração SQLite - 100% GRATUITO PARA SEMPRE
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reagentes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'reagentes-lab-secret-key-2024')
    
    # Inicializar banco
    db.init_app(app)
    
    # Registrar blueprints
    app.register_blueprint(user_bp)
    app.register_blueprint(pedido_bp, url_prefix='/api')
    app.register_blueprint(entrada_bp, url_prefix='/api')
    app.register_blueprint(saida_bp, url_prefix='/api')
    app.register_blueprint(reagente_bp, url_prefix='/api')
    
    # Rotas principais
    @app.route('/')
    def index():
        if 'user_id' not in session:
            return redirect(url_for('user.login'))
        
        user = User.query.get(session['user_id'])
        if user and user.is_admin():
            return redirect(url_for('user.dashboard_admin'))
        else:
            return redirect(url_for('user.dashboard_user'))
    
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Sistema de Reagentes Online - SQLite!'}, 200
    
    # Criar tabelas
    with app.app_context():
        db.create_all()
        
        # Criar usuário admin padrão se não existir
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@reagentes.com',
                tipo='admin'
            )
            admin.set_password('admin123')  # MUDE esta senha em produção!
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuário admin criado: admin / admin123")
    
    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('DEBUG', 'False').lower() == 'true')
