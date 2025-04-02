from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from models import User, Order
from forms import LoginForm, RegistrationForm, ProfileForm

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Login route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Неверный email или пароль', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        
        # Redirect to requested page or home
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.index')
        
        return redirect(next_page)
    
    return render_template('auth/login.html', form=form)

# Logout route
@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

# Register route
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Это имя пользователя уже занято', 'danger')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Этот email уже зарегистрирован', 'danger')
            return redirect(url_for('auth.register'))
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

# Profile route
@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    
    if request.method == 'GET':
        # Pre-fill form with user data
        form.username.data = current_user.username
        form.email.data = current_user.email
    
    if form.validate_on_submit():
        # Check if username changed and exists
        if form.username.data != current_user.username:
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                flash('Это имя пользователя уже занято', 'danger')
                return redirect(url_for('auth.profile'))
        
        # Check if email changed and exists
        if form.email.data != current_user.email:
            existing_email = User.query.filter_by(email=form.email.data).first()
            if existing_email:
                flash('Этот email уже зарегистрирован', 'danger')
                return redirect(url_for('auth.profile'))
        
        # Verify current password if provided
        if form.current_password.data:
            if not current_user.check_password(form.current_password.data):
                flash('Неверный текущий пароль', 'danger')
                return redirect(url_for('auth.profile'))
            
            # Change password if requested
            if form.new_password.data:
                current_user.set_password(form.new_password.data)
        
        # Update user data
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        db.session.commit()
        flash('Профиль успешно обновлен', 'success')
        return redirect(url_for('auth.profile'))
    
    # Get user orders
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    
    return render_template('auth/profile.html', form=form, orders=orders)
