from datetime import datetime, timedelta
from flask import current_app, abort
from flask_login import current_user
from functools import wraps
from app import db
from models import Event, Category, TicketForSale, Contact, Venue, Slide, Review, Order, Ticket, User

# DTO классы для всех моделей для предотвращения detached instance errors
class VenueDTO:
    """Класс передачи данных для площадок"""
    def __init__(self, venue):
        self.id = venue.id
        self.name = venue.name
        self.address = venue.address
        self.city = venue.city
        self.venue_map = venue.venue_map
        self.logo_url = venue.logo_url
        self.logo_path = venue.logo_path
        self.scheme_url = venue.scheme_url
        self.scheme_path = venue.scheme_path
        self.description = venue.description
        self._events_count = None

        # Подсчитываем количество событий сразу при создании DTO
        try:
            from models import Event
            from datetime import datetime
            self._events_count = Event.query.filter(
                Event.venue_id == venue.id,
                Event.date >= datetime.now(),
                Event.is_active == True
            ).count()
        except Exception as e:
            print(f"Error counting events: {e}")
            self._events_count = 0

    def events(self):
        return type('EventCounter', (), {'count': lambda _: self._events_count})()

class CategoryDTO:
    """Класс передачи данных для категорий"""
    def __init__(self, category):
        self.id = category.id
        self.name = category.name
        self.icon = category.icon
        self.icon_image_path = category.icon_image_path if hasattr(category, 'icon_image_path') else None
        self.seo_title = category.seo_title
        self.seo_description = category.seo_description

class EventDTO:
    """Класс передачи данных для событий"""
    def __init__(self, event):
        # Основные атрибуты события
        self.id = event.id
        self.title = event.title
        self.description = event.description
        self.date = event.date
        self.end_date = event.end_date
        self.venue_id = event.venue_id
        self.category_id = event.category_id
        self.base_price = event.base_price
        self.max_price = event.max_price
        self.is_active = event.is_active
        self.is_popular = event.is_popular
        self.is_featured = event.is_featured
        self.image_url = event.image_url
        self.custom_venue_name = event.custom_venue_name
        self.custom_venue_address = event.custom_venue_address
        self.seo_title = event.seo_title
        self.seo_description = event.seo_description
        self.delivery_methods = event.delivery_methods
        
        # Получаем связанную площадку для предотвращения detached instance
        if hasattr(event, 'venue') and event.venue:
            try:
                venue = event.venue
                self.venue = VenueDTO(venue)
            except Exception as e:
                print(f"Ошибка при копировании venue в EventDTO: {e}")
                self.venue = None
        else:
            self.venue = None
        
        # Получаем связанную категорию для предотвращения detached instance
        if hasattr(event, 'category') and event.category:
            try:
                category = event.category
                self.category = CategoryDTO(category)
            except Exception as e:
                print(f"Ошибка при копировании category в EventDTO: {e}")
                self.category = None
        else:
            self.category = None

class SlideDTO:
    """Класс передачи данных для слайдов"""
    def __init__(self, slide):
        self.id = slide.id
        self.title = slide.title
        self.subtitle = slide.subtitle
        self.image_url = slide.image_url
        self.button_text = slide.button_text 
        self.button_url = slide.button_url
        self.order = slide.order
        self.is_active = slide.is_active

class ReviewDTO:
    """Класс передачи данных для отзывов"""
    def __init__(self, review):
        self.id = review.id
        self.user_id = review.user_id
        self.event_id = review.event_id
        self.rating = review.rating
        self.content = review.content
        self.created_at = review.created_at
        self.is_approved = review.is_approved
        
        # Получаем связанные данные
        if hasattr(review, 'user') and review.user:
            try:
                self.user = UserDTO(review.user)
            except:
                self.user = None
        else:
            self.user = None
            
        if hasattr(review, 'event') and review.event:
            try:
                self.event = EventDTO(review.event)
            except:
                self.event = None
        else:
            self.event = None

class UserDTO:
    """Класс передачи данных для пользователей"""
    def __init__(self, user):
        self.id = user.id
        self.username = user.username
        self.email = user.email
        self.registered_on = user.registered_on
        self.is_admin = user.is_admin

class OrderDTO:
    """Класс передачи данных для заказов"""
    def __init__(self, order):
        self.id = order.id
        self.user_id = order.user_id
        self.status = order.status
        self.total_amount = order.total_amount
        self.delivery_method = order.delivery_method
        self.created_at = order.created_at
        self.contact_name = order.contact_name
        self.contact_email = order.contact_email
        self.contact_phone = order.contact_phone
        self.address = order.address
        
        # Связанные данные
        if hasattr(order, 'user') and order.user:
            try:
                self.user = UserDTO(order.user)
            except:
                self.user = None
        else:
            self.user = None
        
        # Элементы заказа
        self.items = []
        if hasattr(order, 'items'):
            try:
                for item in order.items:
                    self.items.append(OrderItemDTO(item))
            except:
                pass

class OrderItemDTO:
    """Класс передачи данных для элементов заказа"""
    def __init__(self, item):
        self.id = item.id
        self.order_id = item.order_id
        self.ticket_id = item.ticket_id
        self.price = item.price
        
        # Связанный билет
        if hasattr(item, 'ticket') and item.ticket:
            try:
                self.ticket = TicketDTO(item.ticket)
            except:
                self.ticket = None
        else:
            self.ticket = None

class TicketDTO:
    """Класс передачи данных для билетов"""
    def __init__(self, ticket):
        self.id = ticket.id
        self.event_id = ticket.event_id
        self.section = ticket.section
        self.row = ticket.row
        self.seat = ticket.seat
        self.price = ticket.price
        self.is_available = ticket.is_available
        self.created_at = ticket.created_at
        
        # Связанное событие
        if hasattr(ticket, 'event') and ticket.event:
            try:
                self.event = EventDTO(ticket.event)
            except:
                self.event = None
        else:
            self.event = None

class TicketForSaleDTO:
    """Класс передачи данных для билетов на продажу"""
    def __init__(self, ticket):
        self.id = ticket.id
        self.user_id = ticket.user_id
        self.event_id = ticket.event_id
        self.event_name = ticket.event_name
        self.venue_name = ticket.venue_name
        self.ticket_type = ticket.ticket_type
        self.section = ticket.section
        self.row = ticket.row
        self.seat = ticket.seat
        self.original_price = ticket.original_price
        self.selling_price = ticket.selling_price
        self.contact_info = ticket.contact_info
        self.created_at = ticket.created_at
        self.status = ticket.status
        
        # Связанные данные
        if hasattr(ticket, 'user') and ticket.user:
            try:
                self.user = UserDTO(ticket.user)
            except:
                self.user = None
        else:
            self.user = None
            
        if hasattr(ticket, 'event') and ticket.event:
            try:
                self.event = EventDTO(ticket.event)
            except:
                self.event = None
        else:
            self.event = None

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
    """
    Получение всех категорий для шаблонов, с исправлением проблемы
    детачмента сессии SQLAlchemy. Используем глобальный класс CategoryDTO.
    """
    # Закрываем текущую сессию для обновления данных
    db.session.expire_all()
    db.session.close()
    
    try:
        # Получаем категории напрямую из базы
        categories = db.session.query(Category).order_by(Category.name).all()
        # Создаем независимые объекты
        return [CategoryDTO(category) for category in categories]
    except Exception as e:
        print(f"Ошибка при получении категорий: {e}")
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


def get_current_user_info():
    """
    Безопасно получает информацию о текущем пользователе,
    избегая проблем с детачментом сессии.
    """
    from flask_login import current_user
    
    # Проверяем, аутентифицирован ли пользователь
    if not current_user.is_authenticated:
        return {
            'username': 'Гость',
            'is_authenticated': False,
            'is_admin': False
        }
    
    # Закрываем текущую сессию для обновления данных
    db.session.expire_all()
    db.session.close()
    
    try:
        # Получаем свежие данные пользователя
        from models import User
        user = db.session.query(User).filter_by(id=current_user.id).first()
        
        if user:
            return {
                'username': user.username,
                'is_authenticated': True,
                'is_admin': user.is_admin,
                'id': user.id
            }
        else:
            return {
                'username': 'Неизвестный пользователь',
                'is_authenticated': True,
                'is_admin': False
            }
    except Exception as e:
        print(f"Ошибка при получении данных пользователя: {e}")
        return {
            'username': 'Ошибка данных',
            'is_authenticated': False,
            'is_admin': False
        }


def get_popular_events():
    """
    Получает популярные события, избегая проблем с детачментом сессии.
    Возвращает список объектов EventDTO с данными о популярных событиях.
    """
    # Обновляем сессию
    db.session.expire_all()
    db.session.close()
    
    try:
        # Получаем популярные события
        events = db.session.query(Event).filter_by(
            is_popular=True, is_active=True
        ).all()
        # Создаем независимые объекты
        return [EventDTO(event) for event in events]
    except Exception as e:
        print(f"Ошибка при получении популярных событий: {e}")
        return []

def get_featured_events():
    """
    Получает избранные события, избегая проблем с детачментом сессии.
    Возвращает список объектов EventDTO с данными о избранных событиях.
    """
    # Обновляем сессию
    db.session.expire_all()
    db.session.close()
    
    try:
        # Получаем фичеринговые события
        events = db.session.query(Event).filter_by(
            is_featured=True, is_active=True
        ).order_by(Event.date).all()
        # Создаем независимые объекты
        return [EventDTO(event) for event in events]
    except Exception as e:
        print(f"Ошибка при получении featured событий: {e}")
        return []

def get_active_slides():
    """
    Получает активные слайды, принудительно обновляя данные
    и избегая проблем с кэшированием SQLAlchemy.
    Создает полные детаченные копии объектов для шаблонов.
    """
    # Закрываем текущую сессию и запрашиваем свежие данные
    db.session.expire_all()
    db.session.close()
    
    # Получаем слайды напрямую из базы и создаем независимые копии
    try:
        # Получаем слайды
        slides = db.session.query(Slide).filter_by(is_active=True).order_by(Slide.order).all()
        # Создаем независимые объекты
        return [SlideDTO(slide) for slide in slides]
    except Exception as e:
        # В случае ошибки возвращаем пустой список
        print(f"Ошибка при получении слайдов: {e}")
        return []