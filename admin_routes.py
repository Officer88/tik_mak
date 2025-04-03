from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
import os
import uuid
import json
from datetime import datetime, timedelta

from app import db
from models import Event, Venue, Category, Ticket, Review, Order, Slide, TicketForSale, Contact, Notification, User
from forms import EventForm, VenueForm, CategoryForm, LoginForm, TicketForm, SlideForm, SellTicketForm, ContactForm, NotificationSettingForm
from helpers import admin_required, get_current_user_info, CategoryDTO, EventDTO, VenueDTO, SlideDTO, ReviewDTO, OrderDTO, TicketDTO, TicketForSaleDTO, UserDTO
from image_utils import save_image, process_image, save_special_format_file

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Декоратор для требования админских прав
@admin_bp.before_request
@login_required
def check_admin():
    try:
        # Получаем ID пользователя
        user_id = int(current_user.get_id())
        
        # Сбросим кэш сессии
        db.session.expire_all()
        
        # Получим свежий экземпляр пользователя
        user = User.query.filter_by(id=user_id).first()
        
        if not user:
            flash('Ошибка при получении данных пользователя', 'danger')
            return redirect(url_for('main.index'))
            
        # Проверяем права администратора
        if not user.is_admin and request.endpoint != 'admin.login':
            flash('У вас нет прав доступа к этой странице', 'danger')
            return redirect(url_for('main.index'))
    except Exception as e:
        print(f"Ошибка при проверке прав администратора: {e}")
        flash('Произошла ошибка при проверке доступа. Пожалуйста, авторизуйтесь снова.', 'danger')
        return redirect(url_for('auth.login'))

# Главная страница админки
@admin_bp.route('/')
def dashboard():
    try:
        # Обновляем сессию для получения свежих данных
        db.session.expire_all()
        
        # Статистика по билетам на продажу
        pending_tickets = db.session.query(TicketForSale).filter_by(status='pending').count()
        confirmed_tickets = db.session.query(TicketForSale).filter_by(status='confirmed').count()
        rejected_tickets = db.session.query(TicketForSale).filter_by(status='rejected').count()
        sold_tickets_resale = db.session.query(TicketForSale).filter_by(status='sold').count()

        # Общая статистика
        event_count = db.session.query(Event).count()
        venue_count = db.session.query(Venue).count()
        category_count = db.session.query(Category).count()
        review_count = db.session.query(Review).count()
        
        # Количество событий на этой неделе
        next_week = datetime.now() + timedelta(days=7)
        upcoming_events = db.session.query(Event).filter(
            Event.date >= datetime.now(),
            Event.date <= next_week
        ).count()
        
        # Статистика по пользователям
        total_users = db.session.query(User).count()
        
        # Статистика по заказам
        total_orders = db.session.query(Order).count()
        completed_orders = db.session.query(Order).filter_by(status='completed').count()
        pending_orders = db.session.query(Order).filter_by(status='pending').count()

        # Статистика по билетам
        available_tickets = db.session.query(Ticket).filter_by(is_available=True).count()
        sold_tickets = db.session.query(Ticket).filter_by(is_available=False).count()
        total_tickets = available_tickets + sold_tickets

        # Последние заказы
        recent_orders = db.session.query(Order).order_by(Order.created_at.desc()).limit(10).all()

        # Статистика по категориям
        categories = db.session.query(Category).all()
        category_stats = []
        for category in categories:
            events = db.session.query(Event).filter_by(category_id=category.id).all()
            event_ids = [event.id for event in events]
            sold_tickets_count = db.session.query(Ticket).filter(
                Ticket.event_id.in_(event_ids) if event_ids else False,
                Ticket.is_available == False
            ).count()
            category_stats.append({
                'name': category.name,
                'sold_tickets': sold_tickets_count
            })

        # Получаем данные о текущем пользователе через Helper-функцию 
        # (исправляет DetachedInstanceError)
        user_info = get_current_user_info()
        admin_username = user_info['username']

        return render_template('admin/dashboard.html',
            total_events=event_count,
            upcoming_events=upcoming_events,
            total_users=total_users,
            total_orders=total_orders,
            completed_orders=completed_orders,
            pending_orders=pending_orders,
            pending_tickets=pending_tickets,
            confirmed_tickets=confirmed_tickets,
            rejected_tickets=rejected_tickets,
            sold_tickets_resale=sold_tickets_resale,
            total_tickets=total_tickets,
            sold_tickets=sold_tickets,
            available_tickets=available_tickets,
            recent_orders=recent_orders,
            category_stats=category_stats,
            admin_username=admin_username,
            event_count=event_count,
            venue_count=venue_count,
            category_count=category_count,
            review_count=review_count
        )
    except Exception as e:
        import logging
        logging.error(f"Ошибка при получении статистики для панели администратора: {e}", exc_info=True)
        
        # Возвращаем шаблон с нулевыми значениями
        return render_template('admin/dashboard.html',
            error="Ошибка при загрузке данных",
            total_events=0,
            upcoming_events=0,
            total_users=0,
            total_orders=0,
            completed_orders=0,
            pending_orders=0,
            pending_tickets=0,
            confirmed_tickets=0,
            rejected_tickets=0,
            sold_tickets_resale=0,
            total_tickets=0,
            sold_tickets=0,
            available_tickets=0,
            recent_orders=[],
            category_stats=[],
            admin_username=current_user.username if current_user else None,
            event_count=0,
            venue_count=0,
            category_count=0,
            review_count=0
        )

# Управление событиями
@admin_bp.route('/events')
def events():
    # Обновляем сессию и получаем события через DTO
    db.session.expire_all()
    db.session.close()

    events = Event.query.order_by(Event.date.desc()).all()
    event_dtos = [EventDTO(event) for event in events]
    return render_template('admin/events.html', events=event_dtos)

# Добавление события
@admin_bp.route('/events/add', methods=['GET', 'POST'])
def add_event():
    form = EventForm()

    # Получаем список категорий для выпадающего списка
    categories = Category.query.all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    # Получаем список площадок для выпадающего списка
    venues = Venue.query.all()
    form.venue_id.choices = [(0, 'Собственная площадка')] + [(v.id, v.name) for v in venues]

    if form.validate_on_submit():
        # Создаем новое событие со всеми полями формы
        event = Event(
            title=form.title.data,
            description=form.description.data,
            date=form.date.data,
            category_id=form.category_id.data,
            base_price=form.base_price.data,
            max_price=form.max_price.data,
            is_active=form.is_active.data,
            is_popular=form.is_popular.data,
            is_featured=form.is_featured.data,
            seo_title=form.seo_title.data or None,
            seo_description=form.seo_description.data or None,
            delivery_methods=','.join(form.delivery_methods.data)
        )

        # Установка даты окончания, если она указана
        if form.end_date.data:
            event.end_date = form.end_date.data

        # Применяем выбор площадки
        if form.venue_id.data > 0:
            event.venue_id = form.venue_id.data
            # Очищаем поля пользовательской площадки
            event.custom_venue_name = None
            event.custom_venue_address = None
        else:
            # Используем пользовательскую площадку
            event.venue_id = None
            event.custom_venue_name = form.custom_venue_name.data
            event.custom_venue_address = form.custom_venue_address.data

        # Обработка изображения
        if form.image_file.data and hasattr(form.image_file.data, 'filename') and form.image_file.data.filename:
            image_url = save_image(form.image_file.data, folder_type='events', max_size=(400, 300))
            if image_url:
                event.image_url = image_url

        # Сохраняем событие в базу данных
        db.session.add(event)
        db.session.commit()

        flash('Событие успешно создано', 'success')
        return redirect(url_for('admin.events'))

    return render_template('admin/edit_event.html', form=form, event=None)

# Редактирование события
@admin_bp.route('/events/edit/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    form = EventForm()

    # Получаем список категорий и площадок для формы
    categories = Category.query.all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    venues = Venue.query.all()
    form.venue_id.choices = [(0, 'Собственная площадка')] + [(v.id, v.name) for v in venues]

    if request.method == 'GET':
        # Заполняем форму данными события
        form.title.data = event.title
        form.description.data = event.description
        form.date.data = event.date
        form.end_date.data = event.end_date
        form.category_id.data = event.category_id

        # Выбор площадки
        if event.venue_id:
            form.venue_id.data = event.venue_id
        else:
            form.venue_id.data = 0
            form.custom_venue_name.data = event.custom_venue_name
            form.custom_venue_address.data = event.custom_venue_address

        form.base_price.data = event.base_price
        form.max_price.data = event.max_price
        form.is_active.data = event.is_active
        form.is_popular.data = event.is_popular
        form.is_featured.data = event.is_featured
        form.seo_title.data = event.seo_title
        form.seo_description.data = event.seo_description

        # Обработка методов доставки
        if event.delivery_methods:
            form.delivery_methods.data = event.delivery_methods.split(',')
        else:
            form.delivery_methods.data = ['email', 'courier']  # Значения по умолчанию

    if form.validate_on_submit():
        # Обновляем данные события
        event.title = form.title.data
        event.description = form.description.data
        event.date = form.date.data
        event.end_date = form.end_date.data if form.end_date.data else None
        event.category_id = form.category_id.data

        # Обновляем информацию о площадке
        if form.venue_id.data > 0:
            event.venue_id = form.venue_id.data
            event.custom_venue_name = None
            event.custom_venue_address = None
        else:
            event.venue_id = None
            event.custom_venue_name = form.custom_venue_name.data
            event.custom_venue_address = form.custom_venue_address.data

        event.base_price = form.base_price.data
        event.max_price = form.max_price.data
        event.is_active = form.is_active.data
        event.is_popular = form.is_popular.data
        event.is_featured = form.is_featured.data
        event.seo_title = form.seo_title.data
        event.seo_description = form.seo_description.data
        event.delivery_methods = ','.join(form.delivery_methods.data)

        # Обработка загруженного изображения
        if form.image_file.data and hasattr(form.image_file.data, 'filename') and form.image_file.data.filename:
            new_image_url = save_image(form.image_file.data, folder_type='events', max_size=(240, 320))
            if new_image_url:
                event.image_url = new_image_url

        db.session.commit()
        flash('Событие успешно обновлено', 'success')
        return redirect(url_for('admin.events'))

    return render_template('admin/edit_event.html', form=form, event=event)

# Удаление события
@admin_bp.route('/events/delete/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Событие успешно удалено', 'success')
    return redirect(url_for('admin.events'))

# Управление площадками
@admin_bp.route('/venues')
def venues():
    try:
        db.session.expire_all()
        db.session.close()
        
        venue_records = Venue.query.all()
        venues = [VenueDTO(venue) for venue in venue_records]
    except Exception as e:
        print(f"Ошибка при получении площадок: {e}")
        venues = []

    return render_template('admin/venues.html', venues=venues)

# Добавление площадки
@admin_bp.route('/venues/add', methods=['GET', 'POST'])
def add_venue():
    form = VenueForm()

    if form.validate_on_submit():
        venue = Venue(
            name=form.name.data,
            address=form.address.data,
            city=form.city.data,
            description=form.description.data
        )

        # Обработка логотипа
        if form.logo_file.data:
            saved_path = save_image(form.logo_file.data, folder_type='venues', max_size=(240, 240))
            if saved_path:
                venue.logo_path = saved_path

        # Обработка схемы зала
        if form.scheme_file.data:
            saved_path = save_image(form.scheme_file.data, folder_type='venues/schemes', max_size=(1200, 1200))
            if saved_path:
                venue.scheme_path = saved_path

        # Сохраняем карту зала, если она указана
        if form.venue_map.data:
            venue.venue_map = form.venue_map.data

        db.session.add(venue)
        db.session.commit()

        flash('Площадка успешно добавлена', 'success')
        return redirect(url_for('admin.venues'))

    return render_template('admin/edit_venue.html', form=form, venue=None)

# Редактирование площадки
@admin_bp.route('/venues/edit/<int:venue_id>', methods=['GET', 'POST'])
def edit_venue(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    form = VenueForm()

    if request.method == 'GET':
        # Заполняем форму данными площадки
        form.name.data = venue.name
        form.address.data = venue.address
        form.city.data = venue.city
        form.description.data = venue.description
        form.venue_map.data = venue.venue_map

    if form.validate_on_submit():
        # Обновляем данные площадки
        venue.name = form.name.data
        venue.address = form.address.data
        venue.city = form.city.data
        venue.description = form.description.data

        # Обработка нового логотипа, если загружен
        if form.logo_file.data:
            saved_path = save_image(form.logo_file.data, folder_type='venues', max_size=(240, 240))
            if saved_path:
                venue.logo_path = saved_path

        # Обработка новой схемы зала, если загружена
        if form.scheme_file.data:
            saved_path = save_image(form.scheme_file.data, folder_type='venues/schemes', max_size=(1200, 1200))
            if saved_path:
                venue.scheme_path = saved_path

        # Обновляем карту зала, если она указана
        if form.venue_map.data is not None:  # Проверяем на None, так как пустая строка - валидное значение
            venue.venue_map = form.venue_map.data

        db.session.commit()
        flash('Площадка успешно обновлена', 'success')
        return redirect(url_for('admin.venues'))

    return render_template('admin/edit_venue.html', form=form, venue=venue)

# Удаление площадки
@admin_bp.route('/venues/delete/<int:venue_id>', methods=['POST'])
def delete_venue(venue_id):
    venue = Venue.query.get_or_404(venue_id)

    # Проверяем, есть ли события, связанные с этой площадкой
    events_count = Event.query.filter_by(venue_id=venue_id).count()
    if events_count > 0:
        flash(f'Невозможно удалить площадку, так как с ней связано {events_count} событий', 'danger')
        return redirect(url_for('admin.venues'))

    db.session.delete(venue)
    db.session.commit()
    flash('Площадка успешно удалена', 'success')
    return redirect(url_for('admin.venues'))

# Управление категориями
@admin_bp.route('/categories')
def categories():
    try:
        # Обновляем сессию перед запросом
        db.session.expire_all()
        db.session.close()

        # Получаем категории
        category_records = Category.query.all()
        categories = [CategoryDTO(category) for category in category_records]

        return render_template('admin/categories.html', categories=categories)
    except Exception as e:
        print(f"Ошибка при получении категорий: {e}")
        return render_template('admin/categories.html', categories=[])

# Добавление категории
@admin_bp.route('/categories/add', methods=['GET', 'POST'])
def add_category():
    form = CategoryForm()

    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            icon=form.icon.data,
            seo_title=form.seo_title.data,
            seo_description=form.seo_description.data
        )

        # Обработка загруженной иконки
        if form.icon_image.data:
            saved_path = save_image(form.icon_image.data, folder_type='categories', max_size=(64, 64))
            if saved_path:
                category.icon_image_path = saved_path

        db.session.add(category)
        db.session.commit()

        flash('Категория успешно добавлена', 'success')
        return redirect(url_for('admin.categories'))

    return render_template('admin/edit_category.html', form=form, category=None)

# Редактирование категории
@admin_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    form = CategoryForm()

    if request.method == 'GET':
        # Заполняем форму данными категории
        form.name.data = category.name
        form.icon.data = category.icon
        form.seo_title.data = category.seo_title
        form.seo_description.data = category.seo_description

    if form.validate_on_submit():
        # Обновляем данные категории
        category.name = form.name.data
        category.icon = form.icon.data
        category.seo_title = form.seo_title.data
        category.seo_description = form.seo_description.data

        # Обработка новой иконки, если загружена
        if form.icon_image.data:
            saved_path = save_image(form.icon_image.data, folder_type='categories', max_size=(64, 64))
            if saved_path:
                category.icon_image_path = saved_path

        db.session.commit()
        flash('Категория успешно обновлена', 'success')
        return redirect(url_for('admin.categories'))

    return render_template('admin/edit_category.html', form=form, category=category)

# Удаление категории
@admin_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)

    # Проверяем, есть ли события в этой категории
    events_count = Event.query.filter_by(category_id=category_id).count()
    if events_count > 0:
        flash(f'Невозможно удалить категорию, так как с ней связано {events_count} событий', 'danger')
        return redirect(url_for('admin.categories'))

    db.session.delete(category)
    db.session.commit()
    flash('Категория успешно удалена', 'success')
    return redirect(url_for('admin.categories'))

# Управление билетами для события
@admin_bp.route('/tickets/<int:event_id>', methods=['GET', 'POST'])
def tickets(event_id):
    event = Event.query.get_or_404(event_id)
    form = TicketForm()

    if form.validate_on_submit():
        # Добавление нового билета
        ticket = Ticket(
            event_id=event_id,
            section=form.section.data,
            row=form.row.data,
            seat=form.seat.data,
            price=form.price.data,
            is_available=form.is_available.data
        )

        db.session.add(ticket)
        db.session.commit()

        flash('Билет успешно добавлен', 'success')
        return redirect(url_for('admin.tickets', event_id=event_id))

    # Получение всех билетов для события
    tickets = Ticket.query.filter_by(event_id=event_id).all()

    return render_template('admin/tickets.html', event=event, tickets=tickets, form=form)

# Удаление билета
@admin_bp.route('/tickets/delete/<int:ticket_id>', methods=['POST'])
def delete_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    event_id = ticket.event_id

    db.session.delete(ticket)
    db.session.commit()

    flash('Билет успешно удален', 'success')
    return redirect(url_for('admin.tickets', event_id=event_id))

# Управление слайдером
@admin_bp.route('/sliders', methods=['GET', 'POST'])
def sliders():
    # Получаем слайды
    slides = Slide.query.order_by(Slide.order).all()
    return render_template('admin/sliders.html', slides=slides)

# Добавление слайда
@admin_bp.route('/sliders/add', methods=['GET', 'POST'])
def add_slide():
    form = SlideForm()

    if form.validate_on_submit():
        slide = Slide(
            title=form.title.data,
            subtitle=form.subtitle.data,
            image_url=form.image_url.data,
            button_text=form.button_text.data,
            button_url=form.button_url.data,
            order=form.order.data or 0,
            is_active=form.is_active.data
        )

        # Обработка загруженного изображения
        if form.image_file.data:
            # Сохраняем и обрабатываем изображение
            saved_path = save_image(
                file_obj=form.image_file.data,
                folder_type='slides',
                max_size=(1200, 600)  # Размер слайдера
            )

            if saved_path:
                slide.image_url = saved_path

        db.session.add(slide)
        db.session.commit()

        flash('Слайд успешно добавлен', 'success')
        return redirect(url_for('admin.sliders'))

    return render_template('admin/sliders.html', form=form, add_mode=True)

@admin_bp.route('/sliders/edit/<int:slide_id>', methods=['GET', 'POST'])
@login_required
def edit_slide(slide_id):
    slide = Slide.query.get_or_404(slide_id)
    form = SlideForm()

    if request.method == 'GET':
        # Pre-fill form with slide data
        form.title.data = slide.title
        form.subtitle.data = slide.subtitle
        form.image_url.data = slide.image_url
        form.button_text.data = slide.button_text
        form.button_url.data = slide.button_url
        form.order.data = slide.order
        form.is_active.data = slide.is_active

    if form.validate_on_submit():
        # Update slide data
        slide.title = form.title.data
        slide.subtitle = form.subtitle.data
        slide.button_text = form.button_text.data
        slide.button_url = form.button_url.data
        slide.order = form.order.data
        slide.is_active = form.is_active.data

        # Only update image_url from form if no uploaded file
        if not form.image_file.data and form.image_url.data:
            slide.image_url = form.image_url.data

        # Handle uploaded image
        if form.image_file.data:
            # Save and process image
            saved_path = save_image(
                file_obj=form.image_file.data,
                folder_type='slides',
                max_size=(1200, 600)  # Slider size
            )

            if saved_path:
                slide.image_url = saved_path

        db.session.commit()
        flash('Слайд успешно обновлен', 'success')
        return redirect(url_for('admin.sliders'))

    return render_template('admin/sliders.html', form=form, slide=slide, add_mode=False)

@admin_bp.route('/sliders/delete/<int:slide_id>', methods=['POST'])
def delete_slide(slide_id):
    slide = Slide.query.get_or_404(slide_id)

    db.session.delete(slide)
    db.session.commit()

    flash('Слайд успешно удален', 'success')
    return redirect(url_for('admin.sliders'))

# Отзывы на модерации
@admin_bp.route('/reviews')
def reviews():
    # Обновляем сессию перед запросом для избежания detached instance
    db.session.expire_all()
    db.session.close()

    try:
        # Получаем отзывы, ожидающие модерации, используя DTO
        pending_review_records = db.session.query(Review).filter_by(is_approved=False).all()
        pending_reviews = [ReviewDTO(review) for review in pending_review_records]

        # Получаем уже одобренные отзывы, используя DTO
        approved_review_records = db.session.query(Review).filter_by(is_approved=True).all()
        approved_reviews = [ReviewDTO(review) for review in approved_review_records]
    except Exception as e:
        print(f"Ошибка при получении отзывов: {e}")
        pending_reviews = []
        approved_reviews = []

    return render_template('admin/reviews.html', 
                          pending_reviews=pending_reviews, 
                          approved_reviews=approved_reviews)

# Одобрение отзыва
@admin_bp.route('/reviews/approve/<int:review_id>', methods=['POST'])
def approve_review(review_id):
    review = Review.query.get_or_404(review_id)
    review.is_approved = True
    db.session.commit()

    flash('Отзыв одобрен', 'success')
    return redirect(url_for('admin.reviews'))

# Отклонение отзыва
@admin_bp.route('/reviews/reject/<int:review_id>', methods=['POST'])
def reject_review(review_id):
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()

    flash('Отзыв отклонен', 'success')
    return redirect(url_for('admin.reviews'))

# Заказы
@admin_bp.route('/orders')
def orders():
    # Обновляем сессию перед запросом для избежания detached instance
    db.session.expire_all()
    db.session.close()

    try:
        # Получаем заказы и используем DTO для предотвращения detached instance
        order_records = db.session.query(Order).order_by(Order.created_at.desc()).all()
        orders = [OrderDTO(order) for order in order_records]
    except Exception as e:
        print(f"Ошибка при получении заказов: {e}")
        orders = []

    return render_template('admin/orders.html', orders=orders)

# Детали заказа
@admin_bp.route('/orders/<int:order_id>')
def order_detail(order_id):
    # Обновляем сессию перед запросом для избежания detached instance
    db.session.expire_all()
    db.session.close()

    try:
        order_record = db.session.query(Order).filter_by(id=order_id).first_or_404()
        order = OrderDTO(order_record)
    except Exception as e:
        print(f"Ошибка при получении заказа: {e}")
        flash('Ошибка при получении данных заказа', 'danger')
        return redirect(url_for('admin.orders'))

    return render_template('admin/order_detail.html', order=order)

# Изменение статуса заказа
@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')

    if new_status in ['pending', 'completed', 'cancelled']:
        order.status = new_status
        db.session.commit()
        flash(f'Статус заказа изменен на {new_status}', 'success')
    else:
        flash('Неверный статус', 'danger')

    return redirect(url_for('admin.order_detail', order_id=order_id))

# Билеты на продажу от пользователей
@admin_bp.route('/tickets-for-sale')
def tickets_for_sale():
    # Обновляем сессию перед запросом для избежания detached instance
    db.session.expire_all()
    db.session.close()

    try:
        # Получаем билеты на продажу и используем DTO для предотвращения detached instance
        ticket_records = db.session.query(TicketForSale).order_by(TicketForSale.created_at.desc()).all()
        tickets = [TicketForSaleDTO(ticket) for ticket in ticket_records]
    except Exception as e:
        print(f"Ошибка при получении билетов на продажу: {e}")
        tickets = []

    return render_template('admin/tickets_for_sale.html', tickets=tickets)

# Подтверждение билета на продажу
@admin_bp.route('/tickets-for-sale/<int:ticket_id>/approve', methods=['POST'])
def approve_ticket_for_sale(ticket_id):
    ticket = TicketForSale.query.get_or_404(ticket_id)
    ticket.status = 'confirmed'
    db.session.commit()

    flash('Билет подтвержден для продажи', 'success')
    return redirect(url_for('admin.tickets_for_sale'))

# Отклонение билета на продажу
@admin_bp.route('/tickets-for-sale/<int:ticket_id>/reject', methods=['POST'])
def reject_ticket_for_sale(ticket_id):
    ticket = TicketForSale.query.get_or_404(ticket_id)
    ticket.status = 'rejected'
    db.session.commit()

    flash('Билет отклонен', 'success')
    return redirect(url_for('admin.tickets_for_sale'))

# Удаление билета на продажу
@admin_bp.route('/tickets-for-sale/<int:ticket_id>/delete', methods=['POST'])
def delete_ticket_for_sale(ticket_id):
    ticket = TicketForSale.query.get_or_404(ticket_id)
    db.session.delete(ticket)
    db.session.commit()

    flash('Билет удален', 'success')
    return redirect(url_for('admin.tickets_for_sale'))

# Управление контактной информацией
@admin_bp.route('/contacts', methods=['GET', 'POST'])
def contacts():
    # Импортируем функцию для получения актуальных контактов
    from helpers import get_contact

    # Получаем контактную информацию с принудительным обновлением данных
    contact = get_contact()

    form = ContactForm(obj=contact)

    if form.validate_on_submit():
        contact.phone = form.phone.data
        contact.email = form.email.data
        contact.telegram = form.telegram.data
        contact.whatsapp = form.whatsapp.data
        contact.vk = form.vk.data
        contact.instagram = form.instagram.data

        # Сохраняем изменения
        db.session.commit()

        # Закрываем сессию и сбрасываем все кэши
        db.session.expire_all()
        db.session.close()

        flash('Контактная информация обновлена', 'success')
        return redirect(url_for('admin.contacts'))

    return render_template('admin/contacts.html', form=form, contact=contact)

# Настройки уведомлений
@admin_bp.route('/notifications', methods=['GET', 'POST'])
def notifications():
    form = NotificationSettingForm()

    if form.validate_on_submit():
        # Здесь можно сохранить настройки уведомлений для админа
        flash('Настройки уведомлений обновлены', 'success')
        return redirect(url_for('admin.notifications'))

    return render_template('admin/notifications.html', form=form)