from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from models import User, Event, Category, Venue, Ticket, Order, Slider, TicketForSale
from forms import EventForm, CategoryForm, VenueForm, SliderForm, TicketForm
from datetime import datetime

# Create blueprint
admin_bp = Blueprint('admin', __name__)

# Admin middleware to check if user is admin
@admin_bp.before_request
def check_admin():
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)

# Admin home page
@admin_bp.route('/')
@login_required
def index():
    # Get statistics
    total_events = Event.query.count()
    total_tickets = Ticket.query.count()
    sold_tickets = Ticket.query.filter_by(is_available=False).count()
    total_users = User.query.count()
    total_orders = Order.query.count()
    
    # Get recent orders
    recent_orders = Order.query.order_by(Order.order_date.desc()).limit(10).all()
    
    # Get sales by category
    categories = Category.query.all()
    category_stats = []
    
    for category in categories:
        events = Event.query.filter_by(category_id=category.id).all()
        event_ids = [event.id for event in events]
        
        sold_tickets_count = Ticket.query.filter(
            Ticket.event_id.in_(event_ids),
            Ticket.is_available == False
        ).count()
        
        category_stats.append({
            'name': category.name,
            'sold_tickets': sold_tickets_count
        })
    
    return render_template('admin/index.html',
                          title='Админ панель',
                          total_events=total_events,
                          total_tickets=total_tickets,
                          sold_tickets=sold_tickets,
                          available_tickets=total_tickets - sold_tickets,
                          total_users=total_users,
                          total_orders=total_orders,
                          recent_orders=recent_orders,
                          category_stats=category_stats)

# Event management
@admin_bp.route('/events')
@login_required
def events():
    events = Event.query.order_by(Event.date.desc()).all()
    return render_template('admin/events.html',
                          title='Управление мероприятиями',
                          events=events)

@admin_bp.route('/events/create', methods=['GET', 'POST'])
@login_required
def create_event():
    form = EventForm()
    
    # Populate select fields
    form.venue_id.choices = [(venue.id, venue.name) for venue in Venue.query.all()]
    form.category_id.choices = [(category.id, category.name) for category in Category.query.all()]
    
    if form.validate_on_submit():
        event = Event(
            title=form.title.data,
            description=form.description.data,
            image_url=form.image_url.data,
            date=form.date.data,
            venue_id=form.venue_id.data,
            category_id=form.category_id.data,
            min_price=form.min_price.data,
            max_price=form.max_price.data,
            is_popular=form.is_popular.data,
            meta_title=form.meta_title.data,
            meta_description=form.meta_description.data
        )
        db.session.add(event)
        db.session.commit()
        
        flash('Мероприятие успешно создано', 'success')
        return redirect(url_for('admin.events'))
    
    return render_template('admin/event_form.html',
                          title='Создать мероприятие',
                          form=form)

@admin_bp.route('/events/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    form = EventForm(obj=event)
    
    # Populate select fields
    form.venue_id.choices = [(venue.id, venue.name) for venue in Venue.query.all()]
    form.category_id.choices = [(category.id, category.name) for category in Category.query.all()]
    
    if form.validate_on_submit():
        event.title = form.title.data
        event.description = form.description.data
        event.image_url = form.image_url.data
        event.date = form.date.data
        event.venue_id = form.venue_id.data
        event.category_id = form.category_id.data
        event.min_price = form.min_price.data
        event.max_price = form.max_price.data
        event.is_popular = form.is_popular.data
        event.meta_title = form.meta_title.data
        event.meta_description = form.meta_description.data
        
        db.session.commit()
        
        flash('Мероприятие успешно обновлено', 'success')
        return redirect(url_for('admin.events'))
    
    return render_template('admin/event_form.html',
                          title='Редактировать мероприятие',
                          form=form,
                          event=event)

@admin_bp.route('/events/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Delete associated tickets first
    Ticket.query.filter_by(event_id=event_id).delete()
    
    db.session.delete(event)
    db.session.commit()
    
    flash('Мероприятие успешно удалено', 'success')
    return redirect(url_for('admin.events'))

@admin_bp.route('/events/<int:event_id>/tickets', methods=['GET', 'POST'])
@login_required
def event_tickets(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Form for adding tickets
    form = TicketForm()
    form.event_id.data = event_id
    
    if form.validate_on_submit():
        # Create multiple tickets
        for i in range(form.quantity.data):
            ticket = Ticket(
                event_id=event_id,
                section=form.section.data,
                row=form.row.data,
                seat=form.seat.data if form.quantity.data == 1 else f"{form.seat.data} {i+1}",
                price=form.price.data,
                is_available=True
            )
            db.session.add(ticket)
        
        db.session.commit()
        flash(f'Добавлено {form.quantity.data} билетов', 'success')
        return redirect(url_for('admin.event_tickets', event_id=event_id))
    
    # Get all tickets for this event
    tickets = Ticket.query.filter_by(event_id=event_id).all()
    
    return render_template('admin/event_tickets.html',
                          title=f'Билеты: {event.title}',
                          event=event,
                          tickets=tickets,
                          form=form)

# Category management
@admin_bp.route('/categories')
@login_required
def categories():
    categories = Category.query.all()
    return render_template('admin/categories.html',
                          title='Управление категориями',
                          categories=categories)

@admin_bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
def create_category():
    form = CategoryForm()
    
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            icon=form.icon.data,
            meta_title=form.meta_title.data,
            meta_description=form.meta_description.data
        )
        db.session.add(category)
        db.session.commit()
        
        flash('Категория успешно создана', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/category_form.html',
                          title='Создать категорию',
                          form=form)

@admin_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.icon = form.icon.data
        category.meta_title = form.meta_title.data
        category.meta_description = form.meta_description.data
        
        db.session.commit()
        
        flash('Категория успешно обновлена', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/category_form.html',
                          title='Редактировать категорию',
                          form=form,
                          category=category)

@admin_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    
    # Check if category has events
    if Event.query.filter_by(category_id=category_id).first():
        flash('Невозможно удалить категорию, к которой привязаны мероприятия', 'danger')
        return redirect(url_for('admin.categories'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash('Категория успешно удалена', 'success')
    return redirect(url_for('admin.categories'))

# Venue management
@admin_bp.route('/venues')
@login_required
def venues():
    venues = Venue.query.all()
    return render_template('admin/venues.html',
                          title='Управление площадками',
                          venues=venues)

@admin_bp.route('/venues/create', methods=['GET', 'POST'])
@login_required
def create_venue():
    form = VenueForm()
    
    if form.validate_on_submit():
        venue = Venue(
            name=form.name.data,
            address=form.address.data,
            city=form.city.data,
            seating_map=form.seating_map.data
        )
        db.session.add(venue)
        db.session.commit()
        
        flash('Площадка успешно создана', 'success')
        return redirect(url_for('admin.venues'))
    
    return render_template('admin/venue_form.html',
                          title='Создать площадку',
                          form=form)

@admin_bp.route('/venues/edit/<int:venue_id>', methods=['GET', 'POST'])
@login_required
def edit_venue(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    form = VenueForm(obj=venue)
    
    if form.validate_on_submit():
        venue.name = form.name.data
        venue.address = form.address.data
        venue.city = form.city.data
        venue.seating_map = form.seating_map.data
        
        db.session.commit()
        
        flash('Площадка успешно обновлена', 'success')
        return redirect(url_for('admin.venues'))
    
    return render_template('admin/venue_form.html',
                          title='Редактировать площадку',
                          form=form,
                          venue=venue)

@admin_bp.route('/venues/delete/<int:venue_id>', methods=['POST'])
@login_required
def delete_venue(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    
    # Check if venue has events
    if Event.query.filter_by(venue_id=venue_id).first():
        flash('Невозможно удалить площадку, к которой привязаны мероприятия', 'danger')
        return redirect(url_for('admin.venues'))
    
    db.session.delete(venue)
    db.session.commit()
    
    flash('Площадка успешно удалена', 'success')
    return redirect(url_for('admin.venues'))

# User management
@admin_bp.route('/users')
@login_required
def users():
    users = User.query.all()
    return render_template('admin/users.html',
                          title='Управление пользователями',
                          users=users)

@admin_bp.route('/users/toggle-admin/<int:user_id>', methods=['POST'])
@login_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    
    # Don't allow changing own admin status
    if user.id == current_user.id:
        flash('Вы не можете изменить свой собственный статус администратора', 'danger')
        return redirect(url_for('admin.users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    flash(f'{"Права администратора предоставлены" if user.is_admin else "Права администратора отозваны"}', 'success')
    return redirect(url_for('admin.users'))

# Slider management
@admin_bp.route('/sliders')
@login_required
def sliders():
    sliders = Slider.query.order_by(Slider.order).all()
    return render_template('admin/sliders.html',
                          title='Управление слайдерами',
                          sliders=sliders)

@admin_bp.route('/sliders/create', methods=['GET', 'POST'])
@login_required
def create_slider():
    form = SliderForm()
    
    if form.validate_on_submit():
        slider = Slider(
            title=form.title.data,
            subtitle=form.subtitle.data,
            image_url=form.image_url.data,
            button_text=form.button_text.data,
            button_url=form.button_url.data,
            order=form.order.data,
            is_active=form.is_active.data
        )
        db.session.add(slider)
        db.session.commit()
        
        flash('Слайд успешно создан', 'success')
        return redirect(url_for('admin.sliders'))
    
    return render_template('admin/slider_form.html',
                          title='Создать слайд',
                          form=form)

@admin_bp.route('/sliders/edit/<int:slider_id>', methods=['GET', 'POST'])
@login_required
def edit_slider(slider_id):
    slider = Slider.query.get_or_404(slider_id)
    form = SliderForm(obj=slider)
    
    if form.validate_on_submit():
        slider.title = form.title.data
        slider.subtitle = form.subtitle.data
        slider.image_url = form.image_url.data
        slider.button_text = form.button_text.data
        slider.button_url = form.button_url.data
        slider.order = form.order.data
        slider.is_active = form.is_active.data
        
        db.session.commit()
        
        flash('Слайд успешно обновлен', 'success')
        return redirect(url_for('admin.sliders'))
    
    return render_template('admin/slider_form.html',
                          title='Редактировать слайд',
                          form=form,
                          slider=slider)

@admin_bp.route('/sliders/delete/<int:slider_id>', methods=['POST'])
@login_required
def delete_slider(slider_id):
    slider = Slider.query.get_or_404(slider_id)
    
    db.session.delete(slider)
    db.session.commit()
    
    flash('Слайд успешно удален', 'success')
    return redirect(url_for('admin.sliders'))

# Orders management
@admin_bp.route('/orders')
@login_required
def orders():
    orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template('admin/orders.html',
                          title='Управление заказами',
                          orders=orders)

@admin_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html',
                          title=f'Заказ #{order.id}',
                          order=order)

# Tickets for sale management
@admin_bp.route('/tickets-for-sale')
@login_required
def tickets_for_sale():
    tickets = TicketForSale.query.order_by(TicketForSale.created_at.desc()).all()
    return render_template('admin/tickets_for_sale.html',
                          title='Билеты от пользователей',
                          tickets=tickets)

@admin_bp.route('/tickets-for-sale/toggle-sold/<int:ticket_id>', methods=['POST'])
@login_required
def toggle_ticket_sold(ticket_id):
    ticket = TicketForSale.query.get_or_404(ticket_id)
    
    ticket.is_sold = not ticket.is_sold
    db.session.commit()
    
    flash(f'Статус билета изменен на {"продан" if ticket.is_sold else "в продаже"}', 'success')
    return redirect(url_for('admin.tickets_for_sale'))
