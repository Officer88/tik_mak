
import os
import logging
import sys
from datetime import datetime

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_migrate import Migrate

# Configure logging with enhanced format and handlers
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

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
    
    # Регистрируем пользовательские фильтры Jinja2
    try:
        from filters import register_filters
        register_filters(app)
        logger.info("Пользовательские фильтры Jinja2 успешно зарегистрированы")
    except Exception as e:
        logger.error(f"Ошибка при регистрации пользовательских фильтров: {e}", exc_info=True)
        print("Запуск приложения без пользовательских фильтров Jinja2")
    
    # Создаем директории для загрузок
    ensure_upload_dirs()
    
    # Register context processors
    from helpers import get_categories, get_pending_tickets_count
    
    @app.context_processor
    def utility_processor():
        # Импортируем функцию из helpers.py
        from helpers import get_contact
        
        # Использование специальной функции для получения всегда свежих данных
        contact = get_contact()
        
        return {
            'get_categories': get_categories,
            'get_pending_tickets_count': get_pending_tickets_count,
            'contact': contact  # Передаем экземпляр с гарантированно свежими данными
        }
    
    # Добавляем функцию-обертку для запросов, чтобы избежать проблем с отсоединенными экземплярами
    @app.before_request
    def before_request():
        # Обновляем сессию перед каждым запросом и логируем запрос для диагностики
        try:
            db.session.expire_all()
            logger.debug(f"Обработка запроса: {request.endpoint} - метод: {request.method}")
        except Exception as e:
            logger.error(f"Ошибка при обработке запроса: {e}", exc_info=True)
            
    # Setup login manager
    @login_manager.user_loader
    def load_user(user_id):
        try:
            # Получаем пользователя через query.filter_by.first() вместо query.get() 
            # для гарантированного получения нового объекта
            db.session.expire_all()
            user = User.query.filter_by(id=int(user_id)).first()
            
            # Обеспечиваем сохранение базовых данных для случаев отсоединения экземпляра
            if user:
                # Сохраняем базовые данные как атрибуты объекта для доступа даже при отсоединении
                user._id = user.id
                user._username = user.username
                user._email = user.email
                user._is_admin = user.is_admin
                logger.info(f"Пользователь {user.id} ({user.username}) успешно загружен")
            else:
                logger.warning(f"Пользователь с ID {user_id} не найден")
                
            return user
        except Exception as e:
            logger.error(f"Критическая ошибка при загрузке пользователя {user_id}: {e}", exc_info=True)
            return None
    
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
