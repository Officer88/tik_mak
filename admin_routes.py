from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from datetime import datetime

from app import db
from models import User, Event, Category, Venue, Ticket, Review, Slide, Order, OrderItem, Contact
from forms import EventForm, CategoryForm, VenueForm, TicketForm, SlideForm, ContactForm

# Create blueprint
admin_bp = Blueprint('admin', __name__)

# Admin required decorator
def admin_required(view_func):
    def wrapped_view(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)  # Forbidden
        return view_func(*args, **kwargs)
    wrapped_view.__name__ = view_func.__name__
    return wrapped_view

# Admin dashboard route
@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    # Count stats
    total_events = Event.query.count()
    upcoming_events = Event.query.filter(Event.date >= datetime.now(), Event.is_active == True).count()
    total_users = User.query.count()
    
    # Orders stats
    total_orders = Order.query.count()
    completed_orders = Order.query.filter_by(status='completed').count()
    pending_orders = Order.query.filter_by(status='pending').count()
    
    # Tickets stats
    total_tickets = Ticket.query.count()
    available_tickets = Ticket.query.filter_by(is_available=True).count()
    sold_tickets = total_tickets - available_tickets
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Recent users
    recent_users = User.query.order_by(User.registered_on.desc()).limit(5).all()
    
    return render_template(
        'admin/dashboard.html',
        total_events=total_events,
        upcoming_events=upcoming_events,
        total_users=total_users,
        total_orders=total_orders,
        completed_orders=completed_orders,
        pending_orders=pending_orders,
        total_tickets=total_tickets,
        available_tickets=available_tickets,
        sold_tickets=sold_tickets,
        recent_orders=recent_orders,
        recent_users=recent_users
    )

# Events management routes
@admin_bp.route('/events')
@login_required
@admin_required
def events():
    events = Event.query.order_by(Event.date.desc()).all()
    return render_template('admin/events.html', events=events)

@admin_bp.route('/events/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_event():
    form = EventForm()
    
    # Populate category select field
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]
    
    # Populate venue select field
    form.venue_id.choices = [(v.id, v.name) for v in Venue.query.order_by(Venue.name).all()]
    
    if form.validate_on_submit():
        event = Event(
            title=form.title.data,
            description=form.description.data,
            image_url=form.image_url.data,
            date=form.date.data,
            end_date=form.end_date.data,
            category_id=form.category_id.data,
            venue_id=form.venue_id.data,
            base_price=form.base_price.data,
            max_price=form.max_price.data,
            is_active=form.is_active.data,
            seo_title=form.seo_title.data,
            seo_description=form.seo_description.data
        )
        
        db.session.add(event)
        db.session.commit()
        
        flash('Мероприятие успешно добавлено', 'success')
        return redirect(url_for('admin.events'))
    
    return render_template('admin/edit_event.html', form=form, title='Добавить мероприятие')

@admin_bp.route('/events/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    form = EventForm()
    
    # Populate category select field
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]
    
    # Populate venue select field
    form.venue_id.choices = [(v.id, v.name) for v in Venue.query.order_by(Venue.name).all()]
    
    if request.method == 'GET':
        # Pre-fill form with event data
        form.title.data = event.title
        form.description.data = event.description
        form.image_url.data = event.image_url
        form.date.data = event.date
        form.end_date.data = event.end_date
        form.category_id.data = event.category_id
        form.venue_id.data = event.venue_id
        form.base_price.data = event.base_price
        form.max_price.data = event.max_price
        form.is_active.data = event.is_active
        form.seo_title.data = event.seo_title
        form.seo_description.data = event.seo_description
    
    if form.validate_on_submit():
        # Update event data
        event.title = form.title.data
        event.description = form.description.data
        event.image_url = form.image_url.data
        event.date = form.date.data
        event.end_date = form.end_date.data
        event.category_id = form.category_id.data
        event.venue_id = form.venue_id.data
        event.base_price = form.base_price.data
        event.max_price = form.max_price.data
        event.is_active = form.is_active.data
        event.seo_title = form.seo_title.data
        event.seo_description = form.seo_description.data
        
        db.session.commit()
        
        flash('Мероприятие успешно обновлено', 'success')
        return redirect(url_for('admin.events'))
    
    return render_template('admin/edit_event.html', form=form, event=event, title='Редактировать мероприятие')

@admin_bp.route('/events/delete/<int:event_id>', methods=['POST'])
@login_required
@admin_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    db.session.delete(event)
    db.session.commit()
    
    flash('Мероприятие успешно удалено', 'success')
    return redirect(url_for('admin.events'))

# Categories management routes
@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@admin_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_category():
    form = CategoryForm()
    
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            icon=form.icon.data,
            seo_title=form.seo_title.data,
            seo_description=form.seo_description.data
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('Категория успешно добавлена', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/categories.html', form=form, add_mode=True)

@admin_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    form = CategoryForm()
    
    if request.method == 'GET':
        # Pre-fill form with category data
        form.name.data = category.name
        form.icon.data = category.icon
        form.seo_title.data = category.seo_title
        form.seo_description.data = category.seo_description
    
    if form.validate_on_submit():
        # Update category data
        category.name = form.name.data
        category.icon = form.icon.data
        category.seo_title = form.seo_title.data
        category.seo_description = form.seo_description.data
        
        db.session.commit()
        
        flash('Категория успешно обновлена', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/categories.html', form=form, category=category, edit_mode=True)

@admin_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    
    # Check if category has events
    if Event.query.filter_by(category_id=category.id).first():
        flash('Невозможно удалить категорию, так как к ней привязаны мероприятия', 'danger')
        return redirect(url_for('admin.categories'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash('Категория успешно удалена', 'success')
    return redirect(url_for('admin.categories'))

# Venues management routes
@admin_bp.route('/venues')
@login_required
@admin_required
def venues():
    venues = Venue.query.all()
    return render_template('admin/venues.html', venues=venues)

@admin_bp.route('/venues/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_venue():
    form = VenueForm()
    
    if form.validate_on_submit():
        venue = Venue(
            name=form.name.data,
            address=form.address.data,
            city=form.city.data,
            description=form.description.data,
            logo_url=form.logo_url.data,
            scheme_url=form.scheme_url.data,
            venue_map=form.venue_map.data
        )
        
        db.session.add(venue)
        db.session.commit()
        
        flash('Площадка успешно добавлена', 'success')
        return redirect(url_for('admin.venues'))
    
    return render_template('admin/venues.html', form=form, add_mode=True)

@admin_bp.route('/venues/edit/<int:venue_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_venue(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    form = VenueForm()
    
    if request.method == 'GET':
        # Pre-fill form with venue data
        form.name.data = venue.name
        form.address.data = venue.address
        form.city.data = venue.city
        form.description.data = venue.description
        form.logo_url.data = venue.logo_url
        form.scheme_url.data = venue.scheme_url
        form.venue_map.data = venue.venue_map
    
    if form.validate_on_submit():
        # Update venue data
        venue.name = form.name.data
        venue.address = form.address.data
        venue.city = form.city.data
        venue.description = form.description.data
        venue.logo_url = form.logo_url.data
        venue.scheme_url = form.scheme_url.data
        venue.venue_map = form.venue_map.data
        
        db.session.commit()
        
        flash('Площадка успешно обновлена', 'success')
        return redirect(url_for('admin.venues'))
    
    return render_template('admin/venues.html', form=form, venue=venue, edit_mode=True)

@admin_bp.route('/venues/delete/<int:venue_id>', methods=['POST'])
@login_required
@admin_required
def delete_venue(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    
    # Check if venue has events
    if Event.query.filter_by(venue_id=venue.id).first():
        flash('Невозможно удалить площадку, так как к ней привязаны мероприятия', 'danger')
        return redirect(url_for('admin.venues'))
    
    db.session.delete(venue)
    db.session.commit()
    
    flash('Площадка успешно удалена', 'success')
    return redirect(url_for('admin.venues'))

# Tickets management routes
@admin_bp.route('/tickets')
@login_required
@admin_required
def tickets():
    event_id = request.args.get('event_id', type=int)
    
    if event_id:
        event = Event.query.get_or_404(event_id)
        tickets = Ticket.query.filter_by(event_id=event_id).all()
        return render_template('admin/tickets.html', tickets=tickets, event=event)
    
    events = Event.query.filter(Event.date >= datetime.now()).order_by(Event.date).all()
    return render_template('admin/tickets.html', events=events)

@admin_bp.route('/tickets/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_ticket():
    form = TicketForm()
    
    # Populate event select field
    form.event_id.choices = [
        (e.id, f"{e.title} ({e.date.strftime('%d.%m.%Y %H:%M')})")
        for e in Event.query.filter(Event.date >= datetime.now()).order_by(Event.date).all()
    ]
    
    if form.validate_on_submit():
        event_id = form.event_id.data
        section = form.section.data
        row = form.row.data
        seat = form.seat.data
        price = form.price.data
        quantity = form.quantity.data or 1
        
        # Add tickets
        for i in range(quantity):
            ticket = Ticket(
                event_id=event_id,
                section=section,
                row=row,
                seat=f"{seat}{i+1}" if quantity > 1 else seat,
                price=price,
                is_available=True
            )
            db.session.add(ticket)
        
        db.session.commit()
        
        flash(f'Успешно добавлено {quantity} билетов', 'success')
        return redirect(url_for('admin.tickets', event_id=event_id))
    
    return render_template('admin/add_ticket.html', form=form)

@admin_bp.route('/tickets/delete/<int:ticket_id>', methods=['POST'])
@login_required
@admin_required
def delete_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    event_id = ticket.event_id
    
    db.session.delete(ticket)
    db.session.commit()
    
    flash('Билет успешно удален', 'success')
    return redirect(url_for('admin.tickets', event_id=event_id))

# Users management route
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/toggle_admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    
    # Don't allow deactivating the current admin
    if user.id == current_user.id:
        flash('Нельзя изменить статус администратора для своего аккаунта', 'warning')
        return redirect(url_for('admin.users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = 'администратора' if user.is_admin else 'пользователя'
    flash(f'Пользователь {user.username} теперь имеет статус {status}', 'success')
    return redirect(url_for('admin.users'))

# Reviews management route
@admin_bp.route('/reviews')
@login_required
@admin_required
def reviews():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template('admin/reviews.html', reviews=reviews)

@admin_bp.route('/reviews/approve/<int:review_id>', methods=['POST'])
@login_required
@admin_required
def approve_review(review_id):
    review = Review.query.get_or_404(review_id)
    
    review.is_approved = True
    db.session.commit()
    
    flash('Отзыв одобрен и опубликован', 'success')
    return redirect(url_for('admin.reviews'))

@admin_bp.route('/reviews/delete/<int:review_id>', methods=['POST'])
@login_required
@admin_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    
    db.session.delete(review)
    db.session.commit()
    
    flash('Отзыв удален', 'success')
    return redirect(url_for('admin.reviews'))

# Sliders management routes
@admin_bp.route('/sliders')
@login_required
@admin_required
def sliders():
    slides = Slide.query.order_by(Slide.order).all()
    return render_template('admin/sliders.html', slides=slides)

@admin_bp.route('/sliders/add', methods=['GET', 'POST'])
@login_required
@admin_required
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
        
        db.session.add(slide)
        db.session.commit()
        
        flash('Слайд успешно добавлен', 'success')
        return redirect(url_for('admin.sliders'))
    
    return render_template('admin/sliders.html', form=form, add_mode=True)

@admin_bp.route('/sliders/edit/<int:slide_id>', methods=['GET', 'POST'])
@login_required
@admin_required
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
        slide.image_url = form.image_url.data
        slide.button_text = form.button_text.data
        slide.button_url = form.button_url.data
        slide.order = form.order.data
        slide.is_active = form.is_active.data
        
        db.session.commit()
        
        flash('Слайд успешно обновлен', 'success')
        return redirect(url_for('admin.sliders'))
    
    return render_template('admin/sliders.html', form=form, slide=slide, edit_mode=True)

@admin_bp.route('/sliders/delete/<int:slide_id>', methods=['POST'])
@login_required
@admin_required
def delete_slide(slide_id):
    slide = Slide.query.get_or_404(slide_id)
    
    db.session.delete(slide)
    db.session.commit()
    
    flash('Слайд успешно удален', 'success')
    return redirect(url_for('admin.sliders'))

@admin_bp.route('/contacts', methods=['GET', 'POST'])
@login_required
@admin_required
def contacts():
    contact = Contact.query.first()
    if not contact:
        contact = Contact(
            phone='+7 (800) 123-45-67',
            email='info@magiktiket.ru',
            telegram='',
            whatsapp='',
            vk='',
            instagram=''
        )
        db.session.add(contact)
        db.session.commit()
    
    form = ContactForm(obj=contact)
    
    if form.validate_on_submit():
        contact.phone = form.phone.data
        contact.email = form.email.data
        contact.telegram = form.telegram.data
        contact.whatsapp = form.whatsapp.data
        contact.vk = form.vk.data
        contact.instagram = form.instagram.data
        
        db.session.commit()
        flash('Контакты успешно обновлены', 'success')
        return redirect(url_for('admin.contacts'))
    
    return render_template('admin/contacts.html', form=form)
