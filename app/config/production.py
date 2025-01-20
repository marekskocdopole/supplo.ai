from app.config.config import Config

class ProductionConfig(Config):
    # Základní nastavení
    DEBUG = False
    TESTING = False
    ENV = 'production'
    
    # Bezpečnostní nastavení
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Cesty k souborům
    UPLOAD_FOLDER = '/var/www/supplo.ai/app/static/uploads'
    DATA_DIR = '/var/www/supplo.ai/app/data'
    
    # Databáze
    SQLALCHEMY_DATABASE_URI = 'sqlite:////var/www/supplo.ai/app.db'  # Pro začátek SQLite, později můžeme přejít na PostgreSQL
    
    # Logování
    LOG_TO_STDOUT = True 