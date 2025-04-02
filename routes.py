from flask import render_template, redirect, url_for, flash, request, session, jsonify, abort
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from models import User, Event, Category, Venue, Ticket, Order, Favorite, Slider, TicketForSale
from forms import LoginForm, RegistrationForm, EventFilterForm, SellTicketForm, CheckoutForm
from utils import get_cart, add_to_cart, update_cart_item, remove_from_cart, clear_cart, get_cart_total
from datetime import datetime

# Home page
@app.route('/')
def index():
    # Get popular and upcoming events
    popular_events = Event.query.filter_by(is_popular=True).order_by(Event.date).limit(6).all()
    upcoming_events = Event.query.filter(Event.date >= datetime.now()).order_by(Event.date).limit(6).all()
    
    # Get active sliders
    sliders = Slider.query.filter_by(is_active=True).order_by(Slider.order).all()
    
    # Get all categories for navigation
    categories = Category.query.all()
    
    return render_template('index.html', 
                          popular_events=popular_events, 
                          upcoming_events=upcoming_events,
                          sliders=sliders,
                          categories=categories)

# User authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неверный email или пароль', 'danger')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    
    return render_template('login.html', title='Вход', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Вы успешно зарегистрировались! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Регистрация', form=form)

# User profile
@app.route('/profile')
@login_required
def profile():
    # Get user's orders
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
    
    # Get user's tickets for sale
    tickets_for_sale = TicketForSale.query.filter_by(user_id=current_user.id).order_by(TicketForSale.created_at.desc()).all()
    
    return render_template('profile.html', 
                          title='Личный кабинет',
                          orders=orders,
                          tickets_for_sale=tickets_for_sale)

# Events routes
@app.route('/events')
def events():
    # Get filter parameters
    category_id = request.args.get('category', type=int)
    venue_id = request.args.get('venue', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    search_query = request.args.get('q')
    page = request.args.get('page', 1, type=int)
    
    # Base query
    query = Event.query.filter(Event.date >= datetime.now())
    
    # Apply filters
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if venue_id:
        query = query.filter_by(venue_id=venue_id)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Event.date >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Event.date <= to_date)
        except ValueError:
            pass
    
    if search_query:
        query = query.filter(Event.title.ilike(f'%{search_query}%'))
    
    # Order by date
    query = query.order_by(Event.date)
    
    # Pagination
    events = query.paginate(page=page, per_page=12, error_out=False)
    
    # Get categories and venues for filter form
    categories = Category.query.all()
    venues = Venue.query.all()
    
    # Create form
    form = EventFilterForm()
    form.category.choices = [(0, 'Все категории')] + [(c.id, c.name) for c in categories]
    form.venue.choices = [(0, 'Все площадки')] + [(v.id, v.name) for v in venues]
    
    return render_template('events.html', 
                          title='Мероприятия',
                          events=events,
                          categories=categories,
                          form=form,
                          search_query=search_query)

@app.route('/events/<int:event_id>')
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Check if event is in favorites
    is_favorite = False
    if current_user.is_authenticated:
        favorite = Favorite.query.filter_by(user_id=current_user.id, event_id=event_id).first()
        is_favorite = favorite is not None
    
    # Get available tickets for this event
    tickets = Ticket.query.filter_by(event_id=event_id, is_available=True).all()
    
    return render_template('event_detail.html',
                          title=event.title,
                          event=event,
                          tickets=tickets,
                          is_favorite=is_favorite)

# Favorites routes
@app.route('/favorites')
@login_required
def favorites():
    # Get user's favorite events
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    favorite_events = [fav.event for fav in favorites]
    
    return render_template('favorites.html',
                          title='Избранное',
                          events=favorite_events)

@app.route('/favorites/add/<int:event_id>', methods=['POST'])
@login_required
def add_to_favorites(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Check if already in favorites
    favorite = Favorite.query.filter_by(user_id=current_user.id, event_id=event_id).first()
    if favorite:
        # Already in favorites, remove it
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'status': 'removed'})
    
    # Add to favorites
    favorite = Favorite(user_id=current_user.id, event_id=event_id)
    db.session.add(favorite)
    db.session.commit()
    
    return jsonify({'status': 'added'})

# Cart routes
@app.route('/cart')
def cart():
    cart_items = get_cart()
    total = get_cart_total()
    
    return render_template('cart.html',
                          title='Корзина',
                          cart=cart_items,
                          total=total)

@app.route('/cart/add/<int:ticket_id>', methods=['POST'])
def cart_add(ticket_id):
    quantity = int(request.form.get('quantity', 1))
    
    if add_to_cart(ticket_id, quantity):
        flash('Билет добавлен в корзину', 'success')
    else:
        flash('Не удалось добавить билет в корзину', 'danger')
    
    return redirect(request.referrer or url_for('cart'))

@app.route('/cart/update/<int:ticket_id>', methods=['POST'])
def cart_update(ticket_id):
    quantity = int(request.form.get('quantity', 1))
    
    if update_cart_item(ticket_id, quantity):
        flash('Корзина обновлена', 'success')
    else:
        flash('Не удалось обновить корзину', 'danger')
    
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:ticket_id>', methods=['POST'])
def cart_remove(ticket_id):
    if remove_from_cart(ticket_id):
        flash('Билет удален из корзины', 'success')
    else:
        flash('Не удалось удалить билет из корзины', 'danger')
    
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    # Redirect if cart is empty
    cart_items = get_cart()
    if not cart_items:
        flash('Ваша корзина пуста', 'warning')
        return redirect(url_for('cart'))
    
    form = CheckoutForm()
    
    # Pre-fill form if user is authenticated
    if current_user.is_authenticated and request.method == 'GET':
        form.email.data = current_user.email
    
    if form.validate_on_submit():
        # Create order
        total = get_cart_total()
        
        if current_user.is_authenticated:
            user_id = current_user.id
        else:
            # Create a temporary user
            temp_user = User(
                username=f"guest_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                email=form.email.data
            )
            temp_user.set_password('temporary')
            db.session.add(temp_user)
            db.session.commit()
            user_id = temp_user.id
        
        # Create order
        order = Order(
            user_id=user_id,
            total_amount=total,
            delivery_method=form.delivery_method.data
        )
        db.session.add(order)
        db.session.commit()
        
        # Update tickets
        for item in cart_items:
            ticket = Ticket.query.get(item['ticket_id'])
            if ticket and ticket.is_available:
                ticket.is_available = False
                ticket.order_id = order.id
        
        db.session.commit()
        
        # Clear cart
        clear_cart()
        
        flash('Ваш заказ успешно оформлен!', 'success')
        if current_user.is_authenticated:
            return redirect(url_for('profile'))
        else:
            return redirect(url_for('index'))
    
    total = get_cart_total()
    return render_template('checkout.html',
                          title='Оформление заказа',
                          form=form,
                          cart=cart_items,
                          total=total)

# Sell ticket route
@app.route('/sell-ticket', methods=['GET', 'POST'])
def sell_ticket():
    form = SellTicketForm()
    
    if form.validate_on_submit():
        ticket = TicketForSale(
            user_id=current_user.id if current_user.is_authenticated else 1,  # Default to admin if not logged in
            event_title=form.event_title.data,
            event_date=form.event_date.data,
            venue=form.venue.data,
            city=form.city.data,
            section=form.section.data,
            row=form.row.data,
            seat=form.seat.data,
            original_price=form.original_price.data,
            asking_price=form.asking_price.data,
            ticket_type=form.ticket_type.data,
            contact_info=form.contact_info.data
        )
        db.session.add(ticket)
        db.session.commit()
        
        flash('Ваш билет размещен на продажу', 'success')
        return redirect(url_for('index'))
    
    return render_template('sell_ticket.html',
                          title='Продать билет',
                          form=form)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
