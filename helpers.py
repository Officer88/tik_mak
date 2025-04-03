from datetime import datetime, timedelta
from flask import current_app, abort
from flask_login import current_user
from functools import wraps
from app import db
from models import Event, Category, TicketForSale, Contact

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def format_date(date):
    """Format date for display in Russian style"""
    if not date:
        return ""
    
    months = [
        'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
        'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
    ]
    
    weekdays = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']
    
    return f"{date.day} {months[date.month-1]}, {weekdays[date.weekday()]}"

def format_time(date):
    """Format time for display"""
    if not date:
        return ""
    
    return date.strftime("%H:%M")

def format_price(price):
    """Format price for display in Russian rubles"""
    if not price:
        return "0 ₽"
    
    return f"{int(price)} ₽"

def get_event_card_date(event):
    """Format date for event card as DD.MM WD"""
    if not event.date:
        return ""
    
    weekdays = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']
    return f"{event.date.day:02d}.{event.date.month:02d} {weekdays[event.date.weekday()]}"

def get_categories():
    """Получение всех категорий для шаблонов"""
    try:
        return Category.query.order_by(Category.name).all()
    except Exception as e:
        current_app.logger.error(f"Ошибка при получении категорий: {e}")
        return []

def clean_old_events():
    """Clean up events that are past their date immediately"""
    cutoff_date = datetime.now()
    old_events = Event.query.filter(Event.date < cutoff_date).all()
    
    for event in old_events:
        # Помечаем событие как неактивное вместо удаления
        event.is_active = False
    
    db.session.commit()
    return len(old_events)

def get_pending_tickets_count():
    """Получение количества билетов, ожидающих подтверждения"""
    try:
        return TicketForSale.query.filter_by(status='pending').count()
    except Exception as e:
        current_app.logger.error(f"Ошибка при получении количества ожидающих билетов: {e}")
        return 0


def get_contact():
    """
    Получает актуальную контактную информацию, принудительно обновляя данные
    и избегая проблем с кэшированием SQLAlchemy.
    """
    # Закрываем текущую сессию и запрашиваем свежие данные
    db.session.expire_all()
    db.session.close()
    
    # Получаем все контакты напрямую из базы
    contacts = db.session.query(Contact).all()
    contact = contacts[0] if contacts else None
    
    # Если запись не найдена, создаем новую
    if not contact:
        contact = Contact(
            phone='+7 (XXX) XXX-XX-XX',
            email='info@example.com'
        )
        db.session.add(contact)
        db.session.commit()
    
    return contact


def get_active_slides():
    """
    Получает активные слайды, принудительно обновляя данные
    и избегая проблем с кэшированием SQLAlchemy.
    Создает полные детаченные копии объектов для шаблонов.
    """
    from models import Slide
    
    class SlideDTO:
        """Класс передачи данных для слайдов, не привязанный к сессии"""
        def __init__(self, slide):
            # Копируем все атрибуты из оригинального объекта
            self.id = slide.id
            self.title = slide.title
            self.subtitle = slide.subtitle
            self.image_url = slide.image_url
            self.button_text = slide.button_text
            self.button_url = slide.button_url
            self.order = slide.order
            self.is_active = slide.is_active
            self.created_at = slide.created_at
    
    # Закрываем текущую сессию и запрашиваем свежие данные
    db.session.expire_all()
    db.session.close()
    
    # Получаем слайды напрямую из базы
    slides = db.session.query(Slide).filter_by(is_active=True).order_by(Slide.order).all()
    
    # Создаем полные независимые копии объектов
    slide_dtos = [SlideDTO(slide) for slide in slides]
    
    # Возвращаем объекты, которые не зависят от сессии
    return slide_dtos
