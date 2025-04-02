import os
import logging
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///biletservice.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database with app
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите, чтобы получить доступ к этой странице.'

# Import models after db initialization to avoid circular imports
with app.app_context():
    # Import models
    from models import User, Event, Category, Venue, Ticket, Order, Favorite, Slider, TicketForSale
    
    # Import routes
    from routes import *
    from admin import admin_bp
    
    # Register blueprints
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Create all tables
    db.create_all()
    
    # Initialize categories if they don't exist
    if Category.query.count() == 0:
        categories = [
            Category(name="Концерты", icon="fa-music"),
            Category(name="Театр", icon="fa-masks-theater"),
            Category(name="Спорт", icon="fa-futbol"),
            Category(name="Выставки", icon="fa-palette"),
            Category(name="Детям", icon="fa-child"),
            Category(name="Кино", icon="fa-film")
        ]
        db.session.add_all(categories)
        db.session.commit()

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Jinja filters
@app.template_filter('format_price')
def format_price(value):
    """Format price in rubles"""
    return f"{int(value)}₽" if value else "Бесплатно"

@app.template_filter('format_date')
def format_date(date):
    """Format date to DD.MM and day of week"""
    if isinstance(date, datetime):
        days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']
        return f"{date.strftime('%d.%m')} {days[date.weekday()]}"
    return date
