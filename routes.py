from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify, abort
from flask_login import current_user, login_required
from datetime import datetime, timedelta
import uuid

from app import db
from models import Event, Category, Venue, Ticket, Review, Favorite, CartItem, TicketForSale, Slide
from forms import EventSearchForm, ReviewForm, CheckoutForm, SellTicketForm

# Create blueprint
main_bp = Blueprint('main', __name__)

# Generate or get session ID for anonymous users
def get_cart_session_id():
    if 'cart_session_id' not in session:
        session['cart_session_id'] = str(uuid.uuid4())
    return session['cart_session_id']

# Home page route
@main_bp.route('/')
def index():
    # Get categories for display
    categories = Category.query.all()
    
    # Get popular events (based on favorites count)
    popular_events = db.session.query(Event, db.func.count(Favorite.id).label('favorite_count')) \
        .join(Favorite, Event.id == Favorite.event_id) \
        .filter(Event.date >= datetime.now(), Event.is_active == True) \
        .group_by(Event.id) \
        .order_by(db.desc('favorite_count')) \
        .limit(4) \
        .all()
    
    # If not enough popular events, get recent events
    if len(popular_events) < 4:
        recent_events = Event.query.filter(
            Event.date >= datetime.now(),
            Event.is_active == True
        ).order_by(Event.date).limit(4 - len(popular_events)).all()
        popular_events.extend([(event, 0) for event in recent_events])
    
    # Get upcoming events
    upcoming_events = Event.query.filter(
        Event.date >= datetime.now(),
        Event.date <= datetime.now() + timedelta(days=7),
        Event.is_active == True
    ).order_by(Event.date).limit(4).all()
    
    # Get active slides
    slides = Slide.query.filter_by(is_active=True).order_by(Slide.order).all()
    
    return render_template(
        'index.html',
        categories=categories,
        popular_events=[e[0] for e in popular_events],
        upcoming_events=upcoming_events,
        slides=slides
    )

# Events catalog route
@main_bp.route('/events')
def events():
    form = EventSearchForm()
    
    # Populate category select field
    form.category.choices = [(0, 'Все категории')] + [
        (c.id, c.name) for c in Category.query.order_by(Category.name).all()
    ]
    
    # Populate venue select field
    form.venue.choices = [(0, 'Все площадки')] + [
        (v.id, v.name) for v in Venue.query.order_by(Venue.name).all()
    ]
    
    # Get filter parameters
    query = request.args.get('query', '')
    category_id = request.args.get('category', type=int)
    venue_id = request.args.get('venue', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    price_min = request.args.get('price_min', type=float)
    price_max = request.args.get('price_max', type=float)
    page = request.args.get('page', 1, type=int)
    
    # Build the query
    query_obj = Event.query.filter(Event.is_active == True)
    
    if query:
        query_obj = query_obj.filter(Event.title.ilike(f'%{query}%'))
    
    if category_id and category_id > 0:
        query_obj = query_obj.filter(Event.category_id == category_id)
    
    if venue_id and venue_id > 0:
        query_obj = query_obj.filter(Event.venue_id == venue_id)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query_obj = query_obj.filter(Event.date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            query_obj = query_obj.filter(Event.date <= date_to_obj)
        except ValueError:
            pass
    
    if price_min is not None:
        query_obj = query_obj.filter(Event.base_price >= price_min)
    
    if price_max is not None:
        query_obj = query_obj.filter(Event.base_price <= price_max)
    
    # Order by date
    query_obj = query_obj.order_by(Event.date)
    
    # Paginate results
    events = query_obj.paginate(page=page, per_page=12, error_out=False)
    
    # Get all categories for filter sidebar
    categories = Category.query.all()
    
    return render_template(
        'catalog.html',
        events=events,
        categories=categories,
        form=form,
        query=query,
        category_id=category_id,
        venue_id=venue_id
    )

# Event details route
@main_bp.route('/event/<int:event_id>')
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    venue = event.venue
    
    # Check if user has this event in favorites
    is_favorite = False
    if current_user.is_authenticated:
        # Check in database for logged-in users
        favorite = Favorite.query.filter_by(user_id=current_user.id, event_id=event.id).first()
        is_favorite = favorite is not None
    else:
        # Check in session for anonymous users
        if 'favorites' in session and session['favorites']:
            is_favorite = event.id in session['favorites']
    
    # Get approved reviews
    reviews = Review.query.filter_by(event_id=event.id, is_approved=True).order_by(Review.created_at.desc()).all()
    
    # Get tickets for this event
    tickets = Ticket.query.filter_by(event_id=event.id, is_available=True).all()
    
    # Get tickets for sale by users
    tickets_for_sale = TicketForSale.query.filter_by(event_id=event.id, is_sold=False).all()
    
    # Create review form
    form = ReviewForm()
    
    return render_template(
        'event.html',
        event=event,
        venue=venue,
        is_favorite=is_favorite,
        reviews=reviews,
        tickets=tickets,
        tickets_for_sale=tickets_for_sale,
        form=form
    )

# Add to favorites route
@main_bp.route('/favorites/add/<int:event_id>', methods=['POST'])
def add_to_favorites(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Check if user is authenticated
    if current_user.is_authenticated:
        # Check if already in favorites
        existing = Favorite.query.filter_by(user_id=current_user.id, event_id=event.id).first()
        if existing:
            flash('Это мероприятие уже в избранном', 'info')
            return redirect(url_for('main.event_detail', event_id=event.id))
        
        # Add to favorites in database
        favorite = Favorite(user_id=current_user.id, event_id=event.id)
        db.session.add(favorite)
        db.session.commit()
    else:
        # Use session for non-authenticated users
        if 'favorites' not in session:
            session['favorites'] = []
            
        # Convert to list in case it's another data type
        favorites = list(session['favorites'])
        
        # Check if already in favorites
        if event_id in favorites:
            flash('Это мероприятие уже в избранном', 'info')
            return redirect(url_for('main.event_detail', event_id=event.id))
            
        # Add to session favorites
        favorites.append(event_id)
        session['favorites'] = favorites
    
    flash('Мероприятие добавлено в избранное', 'success')
    return redirect(url_for('main.event_detail', event_id=event.id))

# Remove from favorites route
@main_bp.route('/favorites/remove/<int:event_id>', methods=['POST'])
def remove_from_favorites(event_id):
    if current_user.is_authenticated:
        # Remove from database
        favorite = Favorite.query.filter_by(user_id=current_user.id, event_id=event_id).first_or_404()
        db.session.delete(favorite)
        db.session.commit()
    else:
        # Remove from session
        if 'favorites' in session:
            favorites = list(session['favorites'])
            if event_id in favorites:
                favorites.remove(event_id)
                session['favorites'] = favorites
    
    flash('Мероприятие удалено из избранного', 'success')
    return redirect(url_for('main.event_detail', event_id=event_id))

# View favorites route
@main_bp.route('/favorites')
def favorites():
    events = []
    
    if current_user.is_authenticated:
        # Get favorites from database
        favorites = Favorite.query.filter_by(user_id=current_user.id).all()
        events = [fav.event for fav in favorites]
    else:
        # Get favorites from session
        if 'favorites' in session and session['favorites']:
            # Convert to list and get unique IDs
            favorite_ids = list(set(session['favorites']))
            # Get events from database using the IDs in session
            events = Event.query.filter(Event.id.in_(favorite_ids)).all()
    
    return render_template('favorites.html', events=events)

# Add to cart route
@main_bp.route('/cart/add/<int:ticket_id>', methods=['POST'])
def add_to_cart(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Check if ticket is available
    if not ticket.is_available:
        flash('Извините, этот билет уже недоступен', 'danger')
        return redirect(url_for('main.event_detail', event_id=ticket.event_id))
    
    # Get session ID for cart
    session_id = get_cart_session_id()
    
    # Check if ticket already in cart
    existing = CartItem.query.filter_by(session_id=session_id, ticket_id=ticket_id).first()
    if existing:
        flash('Этот билет уже в корзине', 'info')
        return redirect(url_for('main.event_detail', event_id=ticket.event_id))
    
    # Add to cart
    cart_item = CartItem(session_id=session_id, ticket_id=ticket_id)
    db.session.add(cart_item)
    db.session.commit()
    
    flash('Билет добавлен в корзину', 'success')
    return redirect(url_for('main.event_detail', event_id=ticket.event_id))

# View cart route
@main_bp.route('/cart')
def view_cart():
    session_id = get_cart_session_id()
    cart_items = CartItem.query.filter_by(session_id=session_id).all()
    
    # Get ticket details
    items = []
    total = 0
    for item in cart_items:
        ticket = item.ticket
        event = ticket.event
        items.append({
            'cart_item_id': item.id,
            'ticket': ticket,
            'event': event
        })
        total += ticket.price
    
    return render_template('cart/cart.html', items=items, total=total)

# Remove from cart route
@main_bp.route('/cart/remove/<int:cart_item_id>', methods=['POST'])
def remove_from_cart(cart_item_id):
    session_id = get_cart_session_id()
    cart_item = CartItem.query.filter_by(id=cart_item_id, session_id=session_id).first_or_404()
    
    db.session.delete(cart_item)
    db.session.commit()
    
    flash('Билет удален из корзины', 'success')
    return redirect(url_for('main.view_cart'))

# Checkout route
@main_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if not current_user.is_authenticated:
        flash('Для оформления заказа необходимо войти в систему', 'warning')
        return redirect(url_for('auth.login', next=url_for('main.checkout')))
    
    # Get cart items
    session_id = get_cart_session_id()
    cart_items = CartItem.query.filter_by(session_id=session_id).all()
    
    if not cart_items:
        flash('Ваша корзина пуста', 'info')
        return redirect(url_for('main.index'))
    
    # Calculate total
    items = []
    total = 0
    for item in cart_items:
        ticket = item.ticket
        event = ticket.event
        items.append({
            'cart_item_id': item.id,
            'ticket': ticket,
            'event': event
        })
        total += ticket.price
    
    form = CheckoutForm()
    
    # Pre-fill form with user data
    if request.method == 'GET':
        form.full_name.data = current_user.username
        form.email.data = current_user.email
    
    if form.validate_on_submit():
        # Process order
        # To be implemented in a future version with payment integration
        flash('Заказ успешно оформлен! Инструкции отправлены на вашу почту.', 'success')
        return redirect(url_for('main.checkout_confirmation'))
    
    return render_template('cart/checkout.html', form=form, items=items, total=total)

# Checkout confirmation route
@main_bp.route('/checkout/confirmation')
@login_required
def checkout_confirmation():
    return render_template('cart/confirmation.html')

# Submit review route
@main_bp.route('/event/<int:event_id>/review', methods=['POST'])
@login_required
def submit_review(event_id):
    event = Event.query.get_or_404(event_id)
    form = ReviewForm()
    
    if form.validate_on_submit():
        # Check if user already reviewed this event
        existing = Review.query.filter_by(user_id=current_user.id, event_id=event.id).first()
        if existing:
            flash('Вы уже оставили отзыв на это мероприятие', 'info')
            return redirect(url_for('main.event_detail', event_id=event.id))
        
        # Create review
        review = Review(
            user_id=current_user.id,
            event_id=event.id,
            rating=form.rating.data,
            content=form.content.data,
            is_approved=False  # Needs admin approval
        )
        db.session.add(review)
        db.session.commit()
        
        flash('Спасибо за отзыв! Он будет опубликован после проверки модератором.', 'success')
    else:
        flash('Ошибка при отправке отзыва. Пожалуйста, проверьте введенные данные.', 'danger')
    
    return redirect(url_for('main.event_detail', event_id=event.id))

# Sell ticket route
@main_bp.route('/sell-ticket', methods=['GET', 'POST'])
def sell_ticket():
    # Получаем event_id из параметров запроса, если он передан
    event_id = request.args.get('event_id', type=int)
    
    form = SellTicketForm()
    
    # Если передан event_id, получаем данные о мероприятии
    event_name = ""
    if request.method == 'GET' and event_id:
        event = Event.query.get(event_id)
        if event:
            event_name = f"{event.title} ({event.date.strftime('%d.%m.%Y %H:%M')})"
            form.event_name.data = event_name
            form.event_id.data = event_id
    
    if form.validate_on_submit():
        # Определяем user_id для билета
        user_id = None
        if current_user.is_authenticated:
            user_id = current_user.id
        
        # Если есть event_id, используем его, иначе создаем заявку без привязки к конкретному событию
        submitted_event_id = form.event_id.data if form.event_id.data else None
        
        ticket = TicketForSale(
            user_id=user_id if user_id else None,
            event_id=submitted_event_id,
            ticket_type=form.ticket_type.data,
            section=form.section.data,
            row=form.row.data,
            seat=form.seat.data,
            original_price=form.original_price.data,
            selling_price=form.selling_price.data,
            contact_info=form.contact_info.data
        )
        db.session.add(ticket)
        db.session.commit()
        
        flash('Ваш билет отправлен на рассмотрение!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('sell_ticket.html', form=form)

# Category events route
@main_bp.route('/category/<int:category_id>')
def category_events(category_id):
    category = Category.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    
    events = Event.query.filter_by(
        category_id=category.id,
        is_active=True
    ).filter(Event.date >= datetime.now()).order_by(Event.date).paginate(
        page=page, per_page=12, error_out=False
    )
    
    return render_template('category_events.html', category=category, events=events)
