"""
Фильтры Jinja2 для шаблонов
"""
import logging
from flask import current_app
from app import db

logger = logging.getLogger(__name__)

def register_filters(app):
    """
    Регистрирует все пользовательские фильтры Jinja2
    """
    @app.template_filter('safe_user_attr')
    def safe_user_attr_filter(user, attr_name):
        """
        Безопасно получает атрибут пользователя, даже если экземпляр отсоединен от сессии
        
        Использование в шаблоне: {{ current_user|safe_user_attr('username') }}
        """
        try:
            # Сначала пробуем получить безопасный атрибут через свойство
            safe_prop_name = f'safe_{attr_name}'
            if hasattr(user, safe_prop_name):
                return getattr(user, safe_prop_name)
                
            # Если нет safe_ свойства, пробуем получить атрибут напрямую
            if hasattr(user, attr_name):
                try:
                    # Убеждаемся что у нас свежая сессия
                    db.session.expire_all()
                    return getattr(user, attr_name)
                except Exception as e:
                    logger.error(f"Ошибка при получении атрибута {attr_name} пользователя: {e}")
                    
                    # Пробуем получить кэшированное значение, если оно есть
                    cached_attr = f'_{attr_name}'
                    if hasattr(user, cached_attr):
                        cached_value = getattr(user, cached_attr)
                        if cached_value is not None:
                            return cached_value
                            
            # Возвращаем значения по умолчанию для разных атрибутов
            defaults = {
                'username': 'Пользователь',
                'email': 'user@example.com',
                'is_admin': False,
                'id': 0
            }
            return defaults.get(attr_name, 'Н/Д')
            
        except Exception as e:
            logger.error(f"Непредвиденная ошибка в safe_user_attr для {attr_name}: {e}")
            return 'Ошибка'

    @app.template_filter('is_admin')
    def is_admin_filter(user):
        """
        Безопасно проверяет, является ли пользователь администратором
        
        Использование в шаблоне: {% if current_user|is_admin %}
        """
        try:
            # Проверяем через safe_is_admin свойство напрямую, если оно есть
            if hasattr(user, 'safe_is_admin'):
                return user.safe_is_admin
                
            # Иначе используем общий метод
            return safe_user_attr_filter(user, 'is_admin')
        except Exception as e:
            logger.error(f"Ошибка при проверке прав администратора: {e}")
            return False
        
    @app.template_filter('user_name')
    def user_name_filter(user):
        """
        Безопасно получает имя пользователя
        
        Использование в шаблоне: {{ current_user|user_name }}
        """
        try:
            # Проверяем через safe_username свойство напрямую, если оно есть
            if hasattr(user, 'safe_username'):
                return user.safe_username
                
            # Иначе используем общий метод
            return safe_user_attr_filter(user, 'username')
        except Exception as e:
            logger.error(f"Ошибка при получении имени пользователя: {e}")
            return "Пользователь"
            
    @app.template_filter('format_price')
    def format_price_filter(value):
        """
        Форматирует цену в удобном для отображения формате
        
        Использование в шаблоне: {{ 1000|format_price }}
        Результат: 1 000 ₽
        """
        if value is None:
            return "0 ₽"
        try:
            # Форматируем число с разделителями тысяч
            formatted = "{:,}".format(int(value)).replace(",", " ")
            return f"{formatted} ₽"
        except Exception as e:
            logger.error(f"Ошибка при форматировании цены {value}: {e}")
            return f"{value} ₽"