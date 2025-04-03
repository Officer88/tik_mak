from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify, abort
from flask_login import current_user, login_required
from datetime import datetime, timedelta
import uuid

from app import db
from models import Event, Category, Venue, Ticket, Review, Favorite, CartItem, TicketForSale, Slide
from forms import EventSearchForm, ReviewForm, CheckoutForm, SellTicketForm
from helpers import get_categories, get_active_slides, get_popular_events, get_featured_events, VenueDTO, EventDTO

# Create blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/reviews')
def reviews():
    reviews = Review.query.filter_by(is_approved=True).order_by(Review.created_at.desc()).all()
    form = ReviewForm() if current_user.is_authenticated else None
    return render_template('reviews.html', reviews=reviews, form=form)

# Generate or get session ID for anonymous users
def get_cart_session_id():
    if 'cart_session_id' not in session:
        session['cart_session_id'] = str(uuid.uuid4())
    return session['cart_session_id']

# Home page route
@main_bp.route('/')
def index():
    # Очистка старых событий (деактивация)
    from helpers import clean_old_events
    clean_old_events()
    
    # Используем helper-функции для получения данных с обработкой detached instance error
    categories = get_categories()
    
    # Получаем популярные события через helper-функцию
    from helpers import get_popular_events
    popular_events = get_popular_events()
    # Если недостаточно популярных событий, добавим дополнительные
    if len(popular_events) < 4:
        # Используем напрямую query, эта проблема не так критична, если не попадаем в шаблон
        try:
            # Обновляем сессию
            db.session.expire_all()
            db.session.close()
            
            recent_events = Event.query.filter(
                Event.date >= datetime.now(),
                Event.is_active == True
            ).order_by(Event.date).limit(4 - len(popular_events)).all()
            
            # Создаем EventDTO для каждого события
            # Импортируем для доступа к классам
            import helpers
            for event in recent_events:
                if len(popular_events) > 0:
                    dto = popular_events[0].__class__(event)
                else:
                    # Если нет ни одного популярного события, создаем "сырой" DTO
                    from helpers import get_popular_events
                    event_dto_class = getattr(helpers, 'EventDTO')
                    dto = event_dto_class(event)
                popular_events.append(dto)
        except Exception as e:
            print(f"Ошибка при получении дополнительных событий: {e}")
    
    # Получаем избранные события через helper-функцию
    upcoming_events = get_featured_events()
    
    # Получаем активные слайды через helper-функцию
    slides = get_active_slides()
    
    # Получаем популярные площадки
    try:
        # Обновляем сессию перед запросом
        db.session.expire_all()
        db.session.close()
        
        venue_records = Venue.query.order_by(
            db.func.random()
        ).limit(8).all()
        venues = [VenueDTO(venue) for venue in venue_records]
    except Exception as e:
        print(f"Ошибка при получении площадок: {e}")
        venues = []
    
    return render_template(
        'index.html',
        categories=categories,
        popular_events=popular_events,
        upcoming_events=upcoming_events,
        slides=slides,
        venues=venues
    )

# Events catalog route
@main_bp.route('/events')
def events():
    # Get filter parameters
    query = request.args.get('query', '')
    category_id = request.args.get('category', type=int)
    venue_id = request.args.get('venue', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    price_min = request.args.get('price_min', type=float)
    price_max = request.args.get('price_max', type=float)
    page = request.args.get('page', 1, type=int)
    
    # Get all categories as dictionaries
    categories = []
    try:
        category_records = Category.query.order_by(Category.name).all()
        for cat in category_records:
            categories.append({
                'id': cat.id,
                'name': cat.name
            })
    except Exception as e:
        import logging
        logging.error(f"Ошибка при получении категорий: {e}")
    
    # Get all venues as dictionaries
    venues = []
    try:
        venue_records = Venue.query.order_by(Venue.name).all()
        for venue in venue_records:
            venues.append({
                'id': venue.id,
                'name': venue.name
            })
    except Exception as e:
        import logging
        logging.error(f"Ошибка при получении площадок: {e}")
    
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
    
    # Обновляем сессию перед запросом
    db.session.expire_all()
    
    # Выполняем запрос и считаем общее количество событий
    event_count = 0
    try:
        event_count = query_obj.count()
    except Exception as e:
        import logging
        logging.error(f"Ошибка при подсчете событий: {e}")
    
    # Рассчитываем пагинацию
    per_page = 12
    total_pages = (event_count + per_page - 1) // per_page if event_count > 0 else 0
    
    # Проверяем валидность номера страницы
    if page < 1 or (total_pages > 0 and page > total_pages):
        page = 1
    
    # Получаем события для текущей страницы
    events_for_page = []
    try:
        paginated_events = query_obj.limit(per_page).offset((page - 1) * per_page).all()
        
        # Безопасно извлекаем данные из событий
        for event in paginated_events:
            event_data = {
                'id': event.id,
                'title': event.title,
                'image_url': event.image_url,
                'base_price': event.base_price,
                'delivery_methods': event.delivery_methods,
                'date': event.date,
                'venue': None
            }
            
            # Если есть площадка, добавляем данные о ней
            if event.venue:
                event_data['venue'] = {
                    'id': event.venue.id,
                    'name': event.venue.name
                }
            
            events_for_page.append(event_data)
    except Exception as e:
        import logging
        logging.error(f"Ошибка при получении событий для страницы: {e}")
    
    return render_template(
        'catalog.html',
        event_list=events_for_page,
        categories=categories,
        venues=venues,
        query=query,
        category_id=category_id,
        venue_id=venue_id,
        current_page=page,
        total_pages=total_pages
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
    success = False
    
    # Check if user is authenticated
    if current_user.is_authenticated:
        # Check if already in favorites
        existing = Favorite.query.filter_by(user_id=current_user.id, event_id=event.id).first()
        if existing:
            # Already in favorites, don't do anything
            success = True
        else:
            # Add to favorites in database
            favorite = Favorite(user_id=current_user.id, event_id=event.id)
            db.session.add(favorite)
            db.session.commit()
            success = True
    else:
        # Use session for non-authenticated users
        if 'favorites' not in session:
            session['favorites'] = []
            
        # Convert to list in case it's another data type
        favorites = list(session['favorites'])
        
        # Check if already in favorites
        if event_id in favorites:
            # Already in favorites, don't do anything
            success = True
        else:    
            # Add to session favorites
            favorites.append(event_id)
            session['favorites'] = favorites
            success = True
    
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': success})
    
    # Regular form submission fallback
    flash('Мероприятие добавлено в избранное', 'success')
    return redirect(url_for('main.event_detail', event_id=event.id))

# Remove from favorites route
@main_bp.route('/favorites/remove/<int:event_id>', methods=['POST'])
def remove_from_favorites(event_id):
    success = False
    
    if current_user.is_authenticated:
        # Remove from database
        favorite = Favorite.query.filter_by(user_id=current_user.id, event_id=event_id).first()
        if favorite:
            db.session.delete(favorite)
            db.session.commit()
            success = True
    else:
        # Remove from session
        if 'favorites' in session:
            favorites = list(session['favorites'])
            if event_id in favorites:
                favorites.remove(event_id)
                session['favorites'] = favorites
                success = True
    
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': success})
    
    # Regular form submission fallback
    flash('Мероприятие удалено из избранного', 'success')
    return redirect(url_for('main.event_detail', event_id=event_id))

# View venue details route
@main_bp.route('/venue/<int:venue_id>')
def venue_detail(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    
    # Создаем DTO для предотвращения detached instance errors
    venue_dto = VenueDTO(venue)
    
    # Получаем предстоящие мероприятия на этой площадке
    events_query = Event.query.filter(
        Event.venue_id == venue_id,
        Event.date >= datetime.now(),
        Event.is_active == True
    ).order_by(Event.date).all()
    
    # Преобразуем события в DTO для предотвращения detached instance errors
    events_dto = [EventDTO(event) for event in events_query]
    
    return render_template('venue.html', venue=venue_dto, events=events_dto)

# View favorites route
@main_bp.route('/favorites')
def favorites():
    events_list = []
    
    if current_user.is_authenticated:
        try:
            # Get favorites from database
            favorites = Favorite.query.filter_by(user_id=current_user.id).all()
            
            # Безопасное получение событий из избранного
            for fav in favorites:
                try:
                    event = Event.query.get(fav.event_id)
                    if event:
                        event_data = {
                            'id': event.id,
                            'title': event.title,
                            'image_url': event.image_url,
                            'base_price': event.base_price,
                            'delivery_methods': event.delivery_methods,
                            'date': event.date,
                            'venue': None
                        }
                        
                        # Если есть площадка, добавляем данные о ней
                        if event.venue:
                            event_data['venue'] = {
                                'id': event.venue.id,
                                'name': event.venue.name
                            }
                        
                        events_list.append(event_data)
                except Exception as e:
                    import logging
                    logging.error(f"Ошибка при получении данных о событии {fav.event_id}: {e}")
        except Exception as e:
            import logging
            logging.error(f"Ошибка при получении избранного: {e}")
    else:
        # Get favorites from session
        if 'favorites' in session and session['favorites']:
            try:
                # Convert to list and get unique IDs
                favorite_ids = list(set(session['favorites']))
                
                # Получаем каждое событие отдельно
                for event_id in favorite_ids:
                    try:
                        event = Event.query.get(event_id)
                        if event:
                            event_data = {
                                'id': event.id,
                                'title': event.title,
                                'image_url': event.image_url,
                                'base_price': event.base_price,
                                'delivery_methods': event.delivery_methods,
                                'date': event.date,
                                'venue': None
                            }
                            
                            # Если есть площадка, добавляем данные о ней
                            if event.venue:
                                event_data['venue'] = {
                                    'id': event.venue.id,
                                    'name': event.venue.name
                                }
                            
                            events_list.append(event_data)
                    except Exception as e:
                        import logging
                        logging.error(f"Ошибка при получении данных о событии {event_id}: {e}")
            except Exception as e:
                import logging
                logging.error(f"Ошибка при обработке сессии избранного: {e}")
    
    return render_template('favorites.html', events=events_list)

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
    form = SellTicketForm()
    
    if request.method == 'POST':
        # Проверяем согласие с правилами
        if not request.form.get('terms_agreement'):
            flash('Необходимо согласиться с правилами сервиса', 'danger')
            return render_template('sell_ticket.html', form=form)

        # Принудительно устанавливаем venue_name и другие поля как None, если они пустые
        if form.venue_name.data == '':
            form.venue_name.data = None
        if form.section.data == '':
            form.section.data = None
        if form.row.data == '':
            form.row.data = None
        if form.seat.data == '':
            form.seat.data = None
            
        if form.validate_on_submit():
            # Определяем user_id для билета
            user_id = None
            if current_user.is_authenticated:
                user_id = current_user.id
            
            try:
                # Создаем билет на продажу без указания event_id (допускается NULL)
                ticket = TicketForSale(
                    user_id=user_id,
                    event_id=None,  # Установка NULL для event_id
                    event_name=form.event_name.data,
                    venue_name=form.venue_name.data,
                    ticket_type=form.ticket_type.data,
                    section=form.section.data,
                    row=form.row.data,
                    seat=form.seat.data,
                    original_price=form.original_price.data,
                    selling_price=form.selling_price.data,
                    contact_info=form.contact_info.data
                )
                
                # Добавляем и сохраняем в БД
                db.session.add(ticket)
                db.session.commit()
                
                # Успешное сообщение и редирект
                flash('Ваш билет отправлен на рассмотрение!', 'success')
                return redirect(url_for('main.index'))
            except Exception as e:
                # Обработка ошибок БД
                db.session.rollback()
                import logging
                logging.error(f"Ошибка при сохранении билета: {str(e)}")
                flash('Произошла ошибка при отправке билета. Пожалуйста, попробуйте еще раз.', 'danger')
        else:
            # Формируем подробное сообщение об ошибках валидации
            error_messages = []
            for field, errors in form.errors.items():
                try:
                    field_label = getattr(form, field).label.text
                    error_msg = f"{field_label}: {', '.join(errors)}"
                    error_messages.append(error_msg)
                except AttributeError:
                    # Fallback для полей без label
                    error_msg = f"{field}: {', '.join(errors)}"
                    error_messages.append(error_msg)
            
            if error_messages:
                flash(f'Ошибки в форме: {"; ".join(error_messages)}', 'danger')
            else:
                flash('Пожалуйста, проверьте правильность заполнения формы', 'danger')
    
    return render_template('sell_ticket.html', form=form)

# Category events route
@main_bp.route('/category/<int:category_id>')
def category_events(category_id):
    try:
        # Пока отключаем страницу категорий и делаем редирект
        # на страницу событий с флагом, что нужно доработать эту страницу
        flash('Страница категории временно недоступна. Ведутся технические работы.', 'info')
        return redirect(url_for('main.events'))
    
    except Exception as e:
        import logging
        logging.error(f"Ошибка при отображении событий категории {category_id}: {e}")
        flash('Произошла ошибка при загрузке категории.', 'danger')
        return redirect(url_for('main.events'))
