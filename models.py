from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import logging

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    registered_on = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Сохраненные копии данных для использования вне сессии
    _username = None
    _email = None
    _is_admin = None
    _id = None
    
    # Relationships
    orders = db.relationship('Order', backref='user', lazy='dynamic')
    favorites = db.relationship('Favorite', backref='user', lazy='dynamic')
    reviews = db.relationship('Review', backref='user', lazy='dynamic')
    tickets_for_sale = db.relationship('TicketForSale', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # Переопределяем геттеры для работы с отсоединенными экземплярами
    def get_id(self):
        """Возвращает идентификатор пользователя для Flask-Login"""
        try:
            return str(self.id)
        except Exception as e:
            logging.error(f"Ошибка при получении ID пользователя: {e}")
            if hasattr(self, '_id') and self._id is not None:
                return str(self._id)
            return "0"
    
    @property
    def safe_username(self):
        """Безопасное получение имени пользователя"""
        try:
            # Сначала пробуем получить кешированное значение, если оно есть
            if hasattr(self, '_username') and self._username is not None:
                return self._username
                
            # Затем пробуем получить атрибут напрямую через сессию
            return self.username
        except Exception as e:
            logging.error(f"Ошибка при получении имени пользователя: {e}")
            # Резервное значение
            return "Пользователь"
    
    @property
    def safe_email(self):
        """Безопасное получение email пользователя"""
        try:
            # Сначала пробуем получить кешированное значение, если оно есть
            if hasattr(self, '_email') and self._email is not None:
                return self._email
                
            # Затем пробуем получить атрибут напрямую через сессию
            return self.email
        except Exception as e:
            logging.error(f"Ошибка при получении email пользователя: {e}")
            # Резервное значение
            return "unknown@example.com"
    
    @property
    def safe_is_admin(self):
        """Безопасное получение статуса администратора"""
        try:
            # Сначала пробуем получить кешированное значение, если оно есть
            if hasattr(self, '_is_admin') and self._is_admin is not None:
                return self._is_admin
                
            # Затем пробуем получить атрибут напрямую через сессию
            return self.is_admin
        except Exception as e:
            logging.error(f"Ошибка при получении статуса администратора: {e}")
            # Резервное значение - False для безопасности
            return False
    
    def __repr__(self):
        return f'<User {self.username}>'


# Event Category model
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    icon = db.Column(db.String(32), nullable=True)
    icon_image_path = db.Column(db.String(256), nullable=True)
    seo_title = db.Column(db.String(100), nullable=True)
    seo_description = db.Column(db.String(200), nullable=True)
    
    # Relationships
    events = db.relationship('Event', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.name}>'


# Venue model
class Venue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    address = db.Column(db.String(256), nullable=False)
    city = db.Column(db.String(64), nullable=False)
    venue_map = db.Column(db.Text, nullable=True)  # Карта зала как текст/SVG
    logo_url = db.Column(db.String(256), nullable=True)  # URL логотипа площадки
    logo_path = db.Column(db.String(256), nullable=True)  # Путь к загруженному логотипу
    scheme_url = db.Column(db.String(256), nullable=True)  # URL схемы площадки
    scheme_path = db.Column(db.String(256), nullable=True)  # Путь к загруженной схеме
    description = db.Column(db.Text, nullable=True)  # Описание площадки
    
    # Relationships
    events = db.relationship('Event', backref='venue', lazy='dynamic')
    
    def __repr__(self):
        return f'<Venue {self.name}, {self.city}>'


# Event model
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(256), nullable=True)
    date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=True)
    custom_venue_name = db.Column(db.String(128), nullable=True)
    custom_venue_address = db.Column(db.String(256), nullable=True)
    is_popular = db.Column(db.Boolean, default=False)  # Популярное мероприятие
    is_featured = db.Column(db.Boolean, default=False)  # Ближайшее/избранное мероприятие
    base_price = db.Column(db.Float, nullable=False)
    max_price = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    seo_title = db.Column(db.String(100), nullable=True)
    seo_description = db.Column(db.String(200), nullable=True)
    delivery_methods = db.Column(db.String(128), default='email,courier')  # Список методов доставки через запятую
    
    # Relationships
    tickets = db.relationship('Ticket', backref='event', lazy='dynamic')
    reviews = db.relationship('Review', backref='event', lazy='dynamic')
    favorites = db.relationship('Favorite', backref='event', lazy='dynamic')
    tickets_for_sale = db.relationship('TicketForSale', 
                                     backref='event', 
                                     lazy='dynamic',
                                     foreign_keys='TicketForSale.event_id')
    
    def __repr__(self):
        return f'<Event {self.title} on {self.date}>'


# Ticket model
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    section = db.Column(db.String(64), nullable=True)
    row = db.Column(db.String(16), nullable=True)
    seat = db.Column(db.String(16), nullable=True)
    price = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='ticket', lazy='dynamic')
    
    def __repr__(self):
        return f'<Ticket {self.id} for Event {self.event_id}>'


# Order model
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(32), default='pending')  # pending, completed, cancelled
    total_amount = db.Column(db.Float, nullable=False)
    delivery_method = db.Column(db.String(32), nullable=False)  # email, courier, event_day, 24h
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    contact_name = db.Column(db.String(128), nullable=False)
    contact_email = db.Column(db.String(128), nullable=False)
    contact_phone = db.Column(db.String(32), nullable=False)
    
    # For courier delivery
    address = db.Column(db.String(256), nullable=True)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy='dynamic')
    
    def __repr__(self):
        return f'<Order {self.id} by User {self.user_id}>'


# Order Item model
class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f'<OrderItem {self.id} for Order {self.order_id}>'


# User Favorites model
class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Favorite Event {self.event_id} for User {self.user_id}>'


# User Reviews model
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Review {self.id} for Event {self.event_id}>'


# Slider model for homepage
class Slide(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    subtitle = db.Column(db.String(200), nullable=True)
    image_url = db.Column(db.String(256), nullable=False)
    button_text = db.Column(db.String(32), nullable=True)
    button_url = db.Column(db.String(256), nullable=True)
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Slide {self.id}: {self.title}>'


# User's Tickets for Sale model
class TicketForSale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Разрешаем NULL для неавторизованных пользователей
    event_id = db.Column(db.Integer, db.ForeignKey('event.id', ondelete='SET NULL'), nullable=True)
    event_name = db.Column(db.String(128), nullable=False)
    venue_name = db.Column(db.String(128), nullable=True)  # Делаем поле необязательным
    ticket_type = db.Column(db.String(32), nullable=False)  # electronic or physical
    section = db.Column(db.String(64), nullable=True)
    row = db.Column(db.String(16), nullable=True)
    seat = db.Column(db.String(16), nullable=True)
    original_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    contact_info = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(32), default='pending')  # pending, confirmed, rejected, sold
    
    def __repr__(self):
        return f'<TicketForSale {self.id} for Event {self.event_name}>'


# Shopping Cart model (for anonymous users)
class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(128), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    ticket = db.relationship('Ticket')
    
    def __repr__(self):
        return f'<CartItem {self.id} for Session {self.session_id}>'

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(128), nullable=False)
    telegram = db.Column(db.String(128), nullable=True)
    whatsapp = db.Column(db.String(32), nullable=True)
    vk = db.Column(db.String(128), nullable=True)
    instagram = db.Column(db.String(128), nullable=True)
    
    def __repr__(self):
        return f'<Contact {self.email}>'
class NotificationSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email_enabled = db.Column(db.Boolean, default=True)
    
    # Связь с пользователем
    user = db.relationship('User', backref=db.backref('notification_settings', lazy=True))
    
    def __repr__(self):
        return f'<NotificationSetting for User {self.user_id}>'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(64), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    related_id = db.Column(db.Integer, nullable=True)  # ID связанной сущности
    
    def __repr__(self):
        return f'<Notification {self.type}: {self.message[:30]}...>'
