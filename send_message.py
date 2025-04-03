import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение учетных данных из переменных окружения
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

def send_twilio_message(to_phone_number: str, message: str) -> dict:
    """
    Отправляет SMS сообщение через Twilio.
    
    Args:
        to_phone_number (str): Номер телефона получателя в формате E.164 (например, +79XXXXXXXXX)
        message (str): Текст сообщения
    
    Returns:
        dict: Словарь с результатом отправки
            {
                'success': True/False, 
                'message': 'Описание результата', 
                'sid': 'ID сообщения (если успешно)'
            }
    """
    # Проверяем наличие учетных данных
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        error_msg = "Отсутствуют учетные данные Twilio. Проверьте переменные окружения."
        logger.error(error_msg)
        return {'success': False, 'message': error_msg}
    
    # Проверяем формат номера телефона
    if not to_phone_number.startswith('+'):
        to_phone_number = '+' + to_phone_number
    
    try:
        # Инициализация клиента Twilio
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Отправка SMS сообщения
        twilio_message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone_number
        )
        
        logger.info(f"Сообщение успешно отправлено. SID: {twilio_message.sid}")
        return {
            'success': True,
            'message': 'Сообщение успешно отправлено',
            'sid': twilio_message.sid
        }
        
    except TwilioRestException as e:
        error_msg = f"Ошибка Twilio: {str(e)}"
        logger.error(error_msg)
        return {'success': False, 'message': error_msg}
        
    except Exception as e:
        error_msg = f"Непредвиденная ошибка при отправке SMS: {str(e)}"
        logger.error(error_msg)
        return {'success': False, 'message': error_msg}


def format_order_notification(order):
    """
    Форматирует уведомление о заказе для отправки по SMS.
    
    Args:
        order: Объект заказа из базы данных
        
    Returns:
        str: Отформатированное сообщение
    """
    message = f"МАГИК ТИКЕТ: Ваш заказ #{order.id} подтвержден\n"
    message += f"Мероприятие: {order.tickets[0].event.title if order.tickets else 'Неизвестно'}\n"
    message += f"Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
    message += f"Сумма: {order.total_price} руб.\n"
    message += "Спасибо за покупку!"
    
    return message


def format_ticket_notification(ticket):
    """
    Форматирует уведомление о билете для отправки по SMS.
    
    Args:
        ticket: Объект билета из базы данных
        
    Returns:
        str: Отформатированное сообщение
    """
    message = f"МАГИК ТИКЕТ: Билет на \"{ticket.event.title}\"\n"
    message += f"Дата: {ticket.event.date.strftime('%d.%m.%Y %H:%M')}\n"
    
    if ticket.section:
        message += f"Секция: {ticket.section}\n"
    if ticket.row:
        message += f"Ряд: {ticket.row}\n"
    if ticket.seat:
        message += f"Место: {ticket.seat}\n"
        
    message += f"Цена: {ticket.price} руб.\n"
    message += "Действителен при предъявлении документа, удостоверяющего личность."
    
    return message