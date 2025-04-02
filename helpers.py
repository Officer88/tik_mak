from datetime import datetime, timedelta
from flask import current_app
from app import db
from models import Event, Category

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
