from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from models.db_models import Admin, db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password_hash, password):
            session['username'] = admin.username
            flash('Успешная авторизация', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неправильный логин или пароль!', 'danger')
    
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if Admin.query.filter_by(username=username).first():
            flash('Данный логин уже занят, попробуйте другой!', 'danger')
            return redirect(url_for('auth.register'))

        new_admin = Admin(username=username, password_hash=generate_password_hash(password))
        db.session.add(new_admin)
        db.session.commit()
        flash('Регистрация прошла успешно.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/logout')
def logout():
    session.pop('username', None)
    flash('Успешный выход из аккаунта', 'success')
    return redirect(url_for('auth.login'))

