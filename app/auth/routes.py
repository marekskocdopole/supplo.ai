from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.auth.forms import LoginForm, RegistrationForm
from app.core.models import User
from app.auth import auth_bp

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        if form.email.data == 'admin' and form.password.data == 'admin':
            # Najít nebo vytvořit admin uživatele
            user = User.query.filter_by(email='admin').first()
            if not user:
                user = User(email='admin', password_hash=generate_password_hash('admin'))
                db.session.add(user)
                db.session.commit()
            
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('index')
            return redirect(next_page)
        
        flash('Nesprávný email nebo heslo', 'danger')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Tento email je již registrován', 'danger')
            return redirect(url_for('auth.register'))
        
        user = User(
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registrace byla úspěšná! Nyní se můžete přihlásit.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Byli jste úspěšně odhlášeni.', 'info')
    return redirect(url_for('auth.login')) 