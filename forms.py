from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms import IntegerField, FloatField, DateTimeField, HiddenField, RadioField, SelectMultipleField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange, ValidationError, Regexp
from datetime import datetime

# Authentication Forms
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

# User Profile Form
class ProfileForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    current_password = PasswordField('Текущий пароль')
    new_password = PasswordField('Новый пароль', validators=[Optional(), Length(min=6)])
    new_password2 = PasswordField('Повторите новый пароль', validators=[EqualTo('new_password')])
    submit = SubmitField('Сохранить')

# Event Search and Filter Form
class EventSearchForm(FlaskForm):
    query = StringField('Поиск', validators=[Optional()])
    category = SelectField('Категория', coerce=int, validators=[Optional()])
    venue = SelectField('Площадка', coerce=int, validators=[Optional()])
    date_from = DateTimeField('С даты', format='%d.%m.%Y', validators=[Optional()])
    date_to = DateTimeField('По дату', format='%d.%m.%Y', validators=[Optional()])
    price_min = FloatField('Мин. цена', validators=[Optional(), NumberRange(min=0)])
    price_max = FloatField('Макс. цена', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Применить фильтры')

# Checkout Form
class CheckoutForm(FlaskForm):
    full_name = StringField('ФИО', validators=[DataRequired(), Length(max=128)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Телефон', validators=[DataRequired(), Length(max=32)])
    delivery_method = RadioField(
        'Способ доставки',
        choices=[
            ('email', 'Электронная почта (моментально)'),
            ('courier', 'Курьером'),
            ('event_day', 'В день мероприятия'),
            ('24h', 'В течение 24 часов на почту')
        ],
        validators=[DataRequired()]
    )
    address = StringField('Адрес доставки', validators=[Optional(), Length(max=256)])
    submit = SubmitField('Оформить заказ')
    
    def validate_address(form, field):
        if form.delivery_method.data == 'courier' and not field.data:
            raise ValidationError('Укажите адрес для курьерской доставки')

# Review Form
class ReviewForm(FlaskForm):
    rating = RadioField('Оценка', choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], coerce=int, validators=[DataRequired()])
    content = TextAreaField('Отзыв', validators=[DataRequired(), Length(min=50, max=1000)])
    photo_url = StringField('URL фотографии (необязательно)', validators=[Optional(), Length(max=256)])
    submit = SubmitField('Отправить отзыв')

# Admin Event Form
class EventForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired(), Length(max=128)])
    description = TextAreaField('Описание', validators=[Optional()])
    image_url = StringField('URL изображения', validators=[Optional(), Length(max=256)])
    image_file = FileField('Загрузить изображение', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')])
    date = DateTimeField('Дата и время', format='%d.%m.%Y %H:%M', validators=[DataRequired()])
    end_date = DateTimeField('Дата и время окончания', format='%d.%m.%Y %H:%M', validators=[Optional()])
    category_id = SelectField('Категория', coerce=int, validators=[DataRequired()])
    venue_type = RadioField('Тип площадки', choices=[
        ('existing', 'Выбрать из существующих'),
        ('custom', 'Указать произвольное место')
    ], default='existing')
    venue_id = SelectField('Площадка', coerce=int, validators=[Optional()])
    custom_venue_name = StringField('Название места', validators=[Optional(), Length(max=128)])
    custom_venue_address = StringField('Адрес', validators=[Optional(), Length(max=256)])
    is_popular = BooleanField('Популярное мероприятие')
    is_featured = BooleanField('Показывать на главной странице')
    base_price = FloatField('Базовая цена', validators=[DataRequired(), NumberRange(min=0)])
    max_price = FloatField('Максимальная цена', validators=[Optional(), NumberRange(min=0)])
    is_active = BooleanField('Активно')
    seo_title = StringField('SEO Заголовок', validators=[Optional(), Length(max=100)])
    seo_description = TextAreaField('SEO Описание', validators=[Optional(), Length(max=200)])
    
    # Выбор методов доставки
    delivery_methods = SelectMultipleField('Способы доставки', choices=[
        ('email', 'Электронный билет (email)'),
        ('courier', 'Курьерская доставка'),
        ('event_day', 'В день мероприятия'),
        ('24h', 'В течение 24 часов')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Сохранить')

# Admin Category Form
class CategoryForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired(), Length(max=64)])
    icon = StringField('Иконка Font Awesome', validators=[Optional(), Length(max=32)])
    icon_image = FileField('Загрузить иконку', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'svg'], 'Только изображения и SVG!')])
    seo_title = StringField('SEO Заголовок', validators=[Optional(), Length(max=100)])
    seo_description = TextAreaField('SEO Описание', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Сохранить')

# Admin Venue Form
class VenueForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired(), Length(max=128)])
    address = StringField('Адрес', validators=[DataRequired(), Length(max=256)])
    city = StringField('Город', validators=[DataRequired(), Length(max=64)])
    description = TextAreaField('Описание площадки', validators=[Optional()])
    logo_url = StringField('URL логотипа', validators=[Optional(), Length(max=256)])
    logo_file = FileField('Загрузить логотип', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')])
    scheme_url = StringField('URL схемы площадки', validators=[Optional(), Length(max=256)])
    scheme_file = FileField('Загрузить схему зала', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'svg'], 'Только изображения и SVG!')])
    venue_map = TextAreaField('Схема зала (SVG)', validators=[Optional()])
    submit = SubmitField('Сохранить')

# Admin Ticket Form
class TicketForm(FlaskForm):
    event_id = SelectField('Мероприятие', coerce=int, validators=[DataRequired()])
    section = StringField('Секция', validators=[Optional(), Length(max=64)])
    row = StringField('Ряд', validators=[Optional(), Length(max=16)])
    seat = StringField('Место', validators=[Optional(), Length(max=16)])
    price = FloatField('Цена', validators=[DataRequired(), NumberRange(min=0)])
    quantity = IntegerField('Количество', validators=[Optional(), NumberRange(min=1)])
    submit = SubmitField('Сохранить')

# Admin Slider Form
class SlideForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired(), Length(max=100)])
    subtitle = StringField('Подзаголовок', validators=[Optional(), Length(max=200)])
    image_url = StringField('URL изображения', validators=[Optional(), Length(max=256)])
    image_file = FileField('Загрузить изображение', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')])
    button_text = StringField('Текст кнопки', validators=[Optional(), Length(max=32)])
    button_url = StringField('URL кнопки', validators=[Optional(), Length(max=256)])
    order = IntegerField('Порядок', validators=[Optional(), NumberRange(min=0)])
    is_active = BooleanField('Активно')
    submit = SubmitField('Сохранить')

# Sell Ticket Form
class ContactForm(FlaskForm):
    phone = StringField('Телефон', validators=[DataRequired(), Length(max=32)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=128)])
    telegram = StringField('Telegram', validators=[Optional(), Length(max=128)])
    whatsapp = StringField('WhatsApp', validators=[Optional(), Length(max=32)])
    vk = StringField('VK', validators=[Optional(), Length(max=128)])
    instagram = StringField('Instagram', validators=[Optional(), Length(max=128)])
    submit = SubmitField('Сохранить')

class SellTicketForm(FlaskForm):
    event_name = StringField('Название мероприятия и дата', validators=[DataRequired(), Length(max=128)])
    venue_name = StringField('Место проведения', validators=[Optional(), Length(max=128)])
    ticket_type = RadioField(
        'Тип билета',
        choices=[
            ('electronic', 'Электронный'),
            ('physical', 'Физический')
        ],
        validators=[DataRequired()]
    )
    section = StringField('Секция', validators=[Optional(), Length(max=64)])
    row = StringField('Ряд', validators=[Optional(), Length(max=16)])
    seat = StringField('Место', validators=[Optional(), Length(max=16)])
    original_price = FloatField('Цена покупки', validators=[DataRequired(), NumberRange(min=0)])
    selling_price = FloatField('Желаемая цена продажи', validators=[DataRequired(), NumberRange(min=0)])
    contact_info = StringField('Контактные данные', validators=[DataRequired(), Length(max=256)])
    submit = SubmitField('Отправить билет на рассмотрение')
class NotificationSettingForm(FlaskForm):
    email_enabled = BooleanField('Отправлять уведомления на email')
    sms_enabled = BooleanField('Отправлять SMS уведомления')
    phone_number = StringField('Номер телефона для SMS (в формате +79XXXXXXXXX)', 
                             validators=[Optional(), Length(max=32), 
                                       Regexp(r'^\+?[0-9]{10,15}$', 
                                             message='Введите корректный номер телефона в формате +79XXXXXXXXX')])
    submit = SubmitField('Сохранить')
