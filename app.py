
import os
import logging
from datetime import datetime

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_migrate import Migrate

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Base class for our models
class Base(DeclarativeBase):
    pass

# Create the app first
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///biletservice.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
migrate = Migrate(app, db)

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'

# Создаем необходимые директории для загрузок файлов
def ensure_upload_dirs():
    upload_dirs = [
        os.path.join('static', 'uploads'),
        os.path.join('static', 'uploads', 'events'),
        os.path.join('static', 'uploads', 'categories'),
        os.path.join('static', 'uploads', 'venues'),
        os.path.join('static', 'uploads', 'venues', 'schemes'),
        os.path.join('static', 'uploads', 'slides'),
    ]
    
    for directory in upload_dirs:
        os.makedirs(directory, exist_ok=True)
        print(f"Убедились, что директория {directory} существует")

# Initialize app context
with app.app_context():
    # Import models to ensure they're registered with SQLAlchemy
    from models import User, Event, Category, Venue, Ticket, Order, OrderItem, Favorite, Review, Slide, TicketForSale, Contact
    
    # Import and register blueprints
    from routes import main_bp
    from auth_routes import auth_bp
    from admin_routes import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Создаем директории для загрузок
    ensure_upload_dirs()
    
    # Register context processors
    from helpers import get_categories, get_pending_tickets_count
    
    @app.context_processor
    def utility_processor():
        return {
            'get_categories': get_categories,
            'get_pending_tickets_count': get_pending_tickets_count,
            'Contact': Contact
        }
    
    # Setup login manager
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create all tables
    db.create_all()
    
    # Add initial categories if they don't exist
    if Category.query.count() == 0:
        categories = [
            {'name': 'Концерты', 'icon': 'fa-music'},
            {'name': 'Театр', 'icon': 'fa-masks-theater'},
            {'name': 'Спорт', 'icon': 'fa-futbol'},
            {'name': 'Выставки', 'icon': 'fa-palette'},
            {'name': 'Детям', 'icon': 'fa-child'},
            {'name': 'Кино', 'icon': 'fa-film'}
        ]
        for cat in categories:
            category = Category(name=cat['name'], icon=cat['icon'])
            db.session.add(category)
        
        # Create admin user if it doesn't exist
        from werkzeug.security import generate_password_hash
        if User.query.filter_by(email='admin@biletservice.ru').first() is None:
            admin = User(
                username='admin',
                email='admin@biletservice.ru',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
        
        db.session.commit()
