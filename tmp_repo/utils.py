from flask import session
from datetime import datetime, timedelta
from models import Event, Ticket, db

def get_cart():
    """Get the current cart from session or initialize a new one"""
    if 'cart' not in session:
        session['cart'] = []
    return session['cart']

def add_to_cart(ticket_id, quantity=1):
    """Add a ticket to the cart"""
    cart = get_cart()
    
    # Check if ticket is already in cart
    for item in cart:
        if item['ticket_id'] == ticket_id:
            item['quantity'] += quantity
            session['cart'] = cart
            return True
    
    # Add new ticket to cart
    ticket = Ticket.query.get(ticket_id)
    if ticket and ticket.is_available:
        cart.append({
            'ticket_id': ticket_id,
            'event_id': ticket.event_id,
            'event_title': ticket.event.title,
            'price': ticket.price,
            'quantity': quantity,
            'section': ticket.section,
            'row': ticket.row,
            'seat': ticket.seat
        })
        session['cart'] = cart
        return True
    return False

def update_cart_item(ticket_id, quantity):
    """Update the quantity of a ticket in the cart"""
    cart = get_cart()
    for item in cart:
        if item['ticket_id'] == ticket_id:
            if quantity <= 0:
                cart.remove(item)
            else:
                item['quantity'] = quantity
            session['cart'] = cart
            return True
    return False

def remove_from_cart(ticket_id):
    """Remove a ticket from the cart"""
    cart = get_cart()
    for item in cart:
        if item['ticket_id'] == ticket_id:
            cart.remove(item)
            session['cart'] = cart
            return True
    return False

def clear_cart():
    """Clear the shopping cart"""
    session.pop('cart', None)

def get_cart_total():
    """Calculate the total price of items in the cart"""
    cart = get_cart()
    return sum(item['price'] * item['quantity'] for item in cart)

def cleanup_expired_events():
    """Delete events that have passed by more than 7 days"""
    cutoff_date = datetime.now() - timedelta(days=7)
    expired_events = Event.query.filter(Event.date < cutoff_date).all()
    
    for event in expired_events:
        # Delete related tickets first
        Ticket.query.filter_by(event_id=event.id).delete()
        
        # Delete the event
        db.session.delete(event)
    
    db.session.commit()
