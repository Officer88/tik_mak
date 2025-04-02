from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='user', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)
    tickets_for_sale = db.relationship('TicketForSale', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

# Event model
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    date = db.Column(db.DateTime, nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    min_price = db.Column(db.Float)
    max_price = db.Column(db.Float)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    is_popular = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # SEO fields
    meta_title = db.Column(db.String(100))
    meta_description = db.Column(db.String(200))
    
    # Relationships
    tickets = db.relationship('Ticket', backref='event', lazy=True)
    favorites = db.relationship('Favorite', backref='event', lazy=True)
    
    def __repr__(self):
        return f'<Event {self.title}>'
    
    @property
    def price_range(self):
        if self.min_price == self.max_price:
            return f"от {int(self.min_price)}₽"
        return f"от {int(self.min_price)}₽ до {int(self.max_price)}₽"

# Category model
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(50))  # Font Awesome icon class
    
    # SEO fields
    meta_title = db.Column(db.String(100))
    meta_description = db.Column(db.String(200))
    
    # Relationships
    events = db.relationship('Event', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'

# Venue model
class Venue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    city = db.Column(db.String(100), nullable=False)
    seating_map = db.Column(db.Text)  # URL or serialized data for the seating map
    
    # Relationships
    events = db.relationship('Event', backref='venue', lazy=True)
    
    def __repr__(self):
        return f'<Venue {self.name}, {self.city}>'

# Ticket model
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    section = db.Column(db.String(50))
    row = db.Column(db.String(20))
    seat = db.Column(db.String(20))
    price = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    
    def __repr__(self):
        return f'<Ticket {self.event_id} - {self.section} {self.row} {self.seat}>'

# Order model
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    delivery_method = db.Column(db.String(50), nullable=False)  # email, courier, event_day, 24h_email
    
    # Relationships
    tickets = db.relationship('Ticket', backref='order', lazy=True)
    
    def __repr__(self):
        return f'<Order {self.id} by User {self.user_id}>'

# Favorite model for wishlisted events
class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Favorite {self.user_id} - {self.event_id}>'

# Slider model for homepage banners
class Slider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    subtitle = db.Column(db.String(200))
    image_url = db.Column(db.String(200), nullable=False)
    button_text = db.Column(db.String(50))
    button_url = db.Column(db.String(200))
    order = db.Column(db.Integer, default=0)  # For sorting
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Slider {self.title}>'

# TicketForSale model for user-to-user ticket sales
class TicketForSale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_title = db.Column(db.String(200), nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    venue = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    section = db.Column(db.String(50))
    row = db.Column(db.String(20))
    seat = db.Column(db.String(20))
    original_price = db.Column(db.Float, nullable=False)
    asking_price = db.Column(db.Float, nullable=False)
    ticket_type = db.Column(db.String(20), nullable=False)  # electronic or physical
    contact_info = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_sold = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<TicketForSale {self.event_title} - {self.user_id}>'
