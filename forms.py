from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField
from wtforms import FloatField, DateTimeField, IntegerField, FileField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError
from datetime import datetime
from models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Пожалуйста, используйте другое имя пользователя.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Пожалуйста, используйте другой email адрес.')

class EventFilterForm(FlaskForm):
    category = SelectField('Категория', choices=[], validators=[Optional()])
    venue = SelectField('Площадка', choices=[], validators=[Optional()])
    date_from = DateTimeField('С даты', format='%Y-%m-%d', validators=[Optional()])
    date_to = DateTimeField('По дату', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Фильтровать')

class SellTicketForm(FlaskForm):
    event_title = StringField('Название мероприятия', validators=[DataRequired()])
    event_date = DateTimeField('Дата мероприятия', format='%Y-%m-%d', validators=[DataRequired()])
    venue = StringField('Площадка', validators=[DataRequired()])
    city = StringField('Город', validators=[DataRequired()])
    section = StringField('Секция', validators=[Optional()])
    row = StringField('Ряд', validators=[Optional()])
    seat = StringField('Место', validators=[Optional()])
    original_price = FloatField('Цена покупки (₽)', validators=[DataRequired()])
    asking_price = FloatField('Желаемая цена продажи (₽)', validators=[DataRequired()])
    ticket_type = SelectField('Тип билета', choices=[
        ('electronic', 'Электронный'),
        ('physical', 'Физический')
    ], validators=[DataRequired()])
    contact_info = StringField('Контактная информация', validators=[DataRequired()])
    submit = SubmitField('Разместить билет')

    def validate_event_date(self, event_date):
        if event_date.data < datetime.now():
            raise ValidationError('Дата мероприятия не может быть в прошлом.')

class CheckoutForm(FlaskForm):
    full_name = StringField('ФИО', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Телефон', validators=[DataRequired()])
    delivery_method = SelectField('Способ доставки', choices=[
        ('email', 'Моментально на email'),
        ('courier', 'Курьером'),
        ('event_day', 'В день мероприятия'),
        ('24h_email', 'В течение 24 часов на email')
    ], validators=[DataRequired()])
    address = StringField('Адрес доставки (для курьера)')
    submit = SubmitField('Оформить заказ')

# Admin forms
class EventForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    image_url = StringField('URL изображения', validators=[DataRequired()])
    date = DateTimeField('Дата и время', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    venue_id = SelectField('Площадка', coerce=int, validators=[DataRequired()])
    category_id = SelectField('Категория', coerce=int, validators=[DataRequired()])
    min_price = FloatField('Минимальная цена', validators=[DataRequired()])
    max_price = FloatField('Максимальная цена', validators=[DataRequired()])
    is_popular = BooleanField('Популярное событие')
    meta_title = StringField('META Title', validators=[Optional()])
    meta_description = TextAreaField('META Description', validators=[Optional()])
    submit = SubmitField('Сохранить')

class CategoryForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    icon = StringField('Иконка (Font Awesome)', validators=[DataRequired()])
    meta_title = StringField('META Title', validators=[Optional()])
    meta_description = TextAreaField('META Description', validators=[Optional()])
    submit = SubmitField('Сохранить')

class VenueForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    address = StringField('Адрес', validators=[DataRequired()])
    city = StringField('Город', validators=[DataRequired()])
    seating_map = TextAreaField('Схема зала', validators=[Optional()])
    submit = SubmitField('Сохранить')

class SliderForm(FlaskForm):
    title = StringField('Заголовок', validators=[Optional()])
    subtitle = StringField('Подзаголовок', validators=[Optional()])
    image_url = StringField('URL изображения', validators=[DataRequired()])
    button_text = StringField('Текст кнопки', validators=[Optional()])
    button_url = StringField('URL кнопки', validators=[Optional()])
    order = IntegerField('Порядок отображения', default=0)
    is_active = BooleanField('Активен', default=True)
    submit = SubmitField('Сохранить')

class TicketForm(FlaskForm):
    event_id = HiddenField('ID события', validators=[DataRequired()])
    section = StringField('Секция', validators=[Optional()])
    row = StringField('Ряд', validators=[Optional()])
    seat = StringField('Место', validators=[Optional()])
    price = FloatField('Цена', validators=[DataRequired()])
    quantity = IntegerField('Количество', default=1)
    submit = SubmitField('Добавить билеты')
