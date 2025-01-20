import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OpenAI konfigurace
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Nastavení uploadů
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Nastavení dat
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    
    # Email konfigurace
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # GitHub konfigurace
    GITHUB_REPO = "marekskocdopole/farm-product-manager"
    
    # Digital Ocean konfigurace
    DO_SERVER = "161.35.70.99"
    
    # Development nastavení
    ENV = 'development'
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    
class DevelopmentConfig(Config):
    ENV = 'development'
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    
class ProductionConfig(Config):
    ENV = 'production'
    DEBUG = False
    TEMPLATES_AUTO_RELOAD = False
    # V produkci by měl být nastaven silný SECRET_KEY
    # SSL/HTTPS nastavení
    # Další produkční nastavení 