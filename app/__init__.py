from flask import Flask, render_template, redirect, url_for, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from app.config.config import Config
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

# Nastavení logování
def setup_logging(app):
    # Vytvoření složky pro logy, pokud neexistuje
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # Nastavení formátu logů
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    
    # Handler pro soubor
    file_handler = RotatingFileHandler(
        'logs/supplo.log', 
        maxBytes=10240,  # 10KB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Handler pro konzoli
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Nastavení základního loggeru
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)
    
    # Nastavení werkzeug loggeru
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.addHandler(file_handler)
    werkzeug_logger.addHandler(console_handler)

    app.logger.info('Inicializace aplikace...')

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Zapnutí debug módu a watchdogu
    if app.config['ENV'] == 'development':
        app.debug = True
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.config['DEBUG'] = True
        app.config['FLASK_DEBUG'] = True
        app.config['USE_RELOADER'] = True
        
    # Nastavení logování
    setup_logging(app)

    # Inicializace rozšíření
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    socketio.init_app(app)

    # Přidání datetime filtru
    @app.template_filter('datetime')
    def format_datetime(value):
        if value is None:
            return ""
        return value.strftime('%d.%m.%Y %H:%M')

    # Registrace blueprintů
    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.blueprints.farms import farms_bp
    app.register_blueprint(farms_bp, url_prefix='/farms')

    from app.blueprints.products import products_bp
    app.register_blueprint(products_bp, url_prefix='/products')

    from app.blueprints.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

    # Hlavní stránka
    @app.route('/')
    def index():
        app.logger.info('Přístup k hlavní stránce')
        stats = {
            'farms_count': 0,
            'active_farms': 0,
            'total_products': 0,
            'confirmed_products': 0,
            'success_rate': 0
        }
        
        try:
            from app.core.models import Farm, Product
            # Počet farem
            stats['farms_count'] = Farm.query.count()
            # Aktivní farmy
            stats['active_farms'] = Farm.query.filter_by(is_active=True).count()
            # Celkový počet produktů
            stats['total_products'] = Product.query.count()
            # Potvrzené produkty
            stats['confirmed_products'] = Product.query.filter_by(is_confirmed=True).count()
            # Úspěšnost
            if stats['total_products'] > 0:
                stats['success_rate'] = round((stats['confirmed_products'] / stats['total_products']) * 100)
        except Exception as e:
            app.logger.error(f'Chyba při načítání statistik: {str(e)}', exc_info=True)
            
        return render_template('dashboard/index.html', stats=stats)

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.error(f'Stránka nenalezena: {request.url}')
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Interní chyba serveru: {str(error)}', exc_info=True)
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.route('/products/<path:farm_id>_images/<filename>')
    def legacy_serve_farm_image(farm_id, filename):
        """Přesměruje staré URL na nové"""
        return redirect(f'/data/farms/{farm_id}/{farm_id}_images/{filename}')

    @app.route('/data/farms/<path:farm_id>/<path:farm_id>_images/<filename>')
    def serve_farm_image(farm_id, filename):
        """Servíruje obrázky z adresáře farmy"""
        if app.config['ENV'] == 'production':
            # Použijeme absolutní cestu
            images_path = f'/var/www/supplo.ai/app/data/farms/{farm_id}/{farm_id}_images'
            app.logger.info(f'Serving image from: {images_path}/{filename}')
            return send_from_directory(images_path, filename)
        else:
            images_path = os.path.join(os.path.dirname(__file__), 'data', 'farms', farm_id, f'{farm_id}_images')
            return send_from_directory(images_path, filename)

    app.logger.info('Aplikace byla úspěšně inicializována')
    return app 