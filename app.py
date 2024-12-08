from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from models.database import db
from auth import auth_bp
import models.db_models as dbm
from sqlalchemy.exc import IntegrityError
from flask import flash
from sqlalchemy import func

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:240404@localhost/top_valenki'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret123'

db.init_app(app)
app.register_blueprint(auth_bp)

with app.app_context():
    db.create_all()


@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html')
    else:
        return redirect(url_for('auth.login'))

# @app.route('/employees', methods=['GET'])
# def get_employees():
#     employees = dbm.Employees.query.all()
#     return render_template('get_employees.html', employees=employees)

@app.route('/employees', methods=['GET'])
def employees_filter():
    employee_name = request.args.get('employee_name', '')
    employee_surname = request.args.get('employee_surname', '')
    birthday = request.args.get('birthday', '')
    post = request.args.get('post', '')
    print(request.args)
    query = dbm.Employees.query
    
    if employee_name:
        query = query.filter(dbm.Employees.name.ilike(f"%{employee_name}%"))
    if employee_surname:
        query = query.filter(dbm.Employees.surname.ilike(f"%{employee_surname}%"))
    if birthday:
        query = query.filter(dbm.Employees.birthday.ilike(f"%{birthday}%"))
    if post:
        query = query.filter(dbm.Employees.post.ilike(f"%{post}%"))

    employees = query.all()

    return render_template('get_employees.html', employees=employees)

@app.route('/clients', methods=['GET'])
def clients_filter():
    client_name = request.args.get('client_name', '')
    client_surname = request.args.get('client_surname', '')
    status = request.args.get('status', '')

    query = dbm.Clients.query
    
    if client_name:
        query = query.filter(dbm.Clients.name.ilike(f"%{client_name}%"))
    if client_surname:
        query = query.filter(dbm.Clients.surname.ilike(f"%{client_surname}%"))
    if status:
        query = query.filter(dbm.Clients.importance == status)

    clients = query.all()

    return render_template('get_clients.html', clients=clients)


@app.route('/orders', methods=['GET'])
def orders_filter():
    client_name = request.args.get('client_name', '')
    employee_name = request.args.get('employee_name', '')
    status = request.args.get('status', '')
    cost = request.args.get('cost', '')
    
    query = dbm.Orders.query.join(dbm.Clients, dbm.Orders.idCl == dbm.Clients.id) \
                    .join(dbm.Employees, dbm.Orders.idEm == dbm.Employees.id) \
                    .add_columns(dbm.Clients.name.label('client_name'),
                                    dbm.Employees.name.label('employee_name'),
                                    dbm.Orders.id,
                                    dbm.Orders.compound,
                                    dbm.Orders.status,
                                    dbm.Orders.cost)
    
    if client_name:
        query = query.filter(dbm.Clients.name.ilike(f"%{client_name}%"))
    if employee_name:
        query = query.filter(dbm.Employees.name.ilike(f"%{employee_name}%"))
    if status:
        query = query.filter(dbm.Orders.status == status)
    if cost:
        cost = cost.strip()
        operator = ''
        number = 0

        for oper in [">=", "<=", ">", "<", "=", "!=", "="]:
            if cost.startswith(oper):
                number_str = cost[len(oper):].strip()
                operator = oper
                number = int(number_str)

        if operator == ">":
            query = query.filter(dbm.Orders.cost > number)
        elif operator == "<":
            query = query.filter(dbm.Orders.cost < number)
        elif operator == "=" or operator == "==":
            query = query.filter(dbm.Orders.cost == number)
        elif operator == ">=":
            query = query.filter(dbm.Orders.cost >= number)
        elif operator == "<=":
            query = query.filter(dbm.Orders.cost <= number)
        elif operator == "!=":
            query = query.filter(dbm.Orders.cost != number)

    orders = query.all()

    return render_template('orders.html', orders=orders)




@app.route('/add_client', methods=['POST'])
def add_client():
    client_name = request.form.get('name', '')
    client_surname = request.form.get('surname', '')
    status = request.form.get('status', '')
    
    if not client_name or not client_surname or not status:
        flash("Все поля формы должны быть заполнены.", "warning")
        return redirect(url_for('clients_filter'))
    
    normalized_name = client_name.strip().lower()
    normalized_surname = client_surname.strip().lower()

    existing_client = dbm.Clients.query.filter(
        func.lower(dbm.Clients.name) == normalized_name,
        func.lower(dbm.Clients.surname) == normalized_surname
    ).first()

    if existing_client:
        flash("Клиент с таким именем и фамилией уже существует.", "warning")
    else:
        new_client = dbm.Clients(name=client_name, surname=client_surname, importance=status)
        db.session.add(new_client)
        db.session.commit()
        flash("Клиент успешно добавлен!", "success")
    return redirect(url_for('clients_filter'))


@app.route('/delete_client', methods=['POST'])
def delete_client():
    client_id = request.form.get('id')
    if client_id:
        try:
            client = dbm.Clients.query.get(client_id)
            if client:
                db.session.delete(client)
                db.session.commit()
                flash("Клиент успешно удалён.", "success")
            else:
                flash("Клиент с таким ID не найден.", "warning")
        except IntegrityError:
            db.session.rollback()
            flash("Невозможно удалить клиента, поскольку он связан с другими записями. Сначала удалите связанные данные.", "warning")
    else:
        flash("Некорректный ID клиента.", "error")
    return redirect(url_for('clients_filter'))


def validate_date(date_string):
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False


@app.route('/add_employee', methods=['POST'])
def add_employee():
    employee_name = request.form.get('name', '')
    employee_surname = request.form.get('surname', '')
    birthday = request.form.get('birthday', '')
    post = request.form.get('post', '')

    if not employee_name or not employee_surname or not birthday or not post:
        flash("Все поля формы должны быть заполнены.", "warning")
        return redirect(url_for('employees_filter'))
    
    if not validate_date(birthday):
        flash("Введите дату в формате YYYY-MM-DD.", "warning")
        return redirect(url_for('employees_filter'))
    
    normalized_name = employee_name.strip().lower()
    normalized_surname = employee_surname.strip().lower()

    existing_client = dbm.Employees.query.filter(
        func.lower(dbm.Employees.name) == normalized_name,
        func.lower(dbm.Employees.surname) == normalized_surname
    ).first()

    if existing_client:
        flash("Клиент с таким именем и фамилией уже существует.", "warning")
    else:
        new_employee = dbm.Employees(name=employee_name, surname=employee_surname, birthday=birthday, post=post)
        db.session.add(new_employee)
        db.session.commit()
        flash("Сотрудник успешно добавлен!", "success")
    return redirect(url_for('employees_filter'))


@app.route('/delete_employee', methods=['POST'])
def delete_emplyee():
    employee_id = request.form.get('id')
    if employee_id:
        try:
            client = dbm.Employees.query.get(employee_id)
            if client:
                db.session.delete(client)
                db.session.commit()
                flash("Сотрудник успешно удалён.", "success")
            else:
                flash("Сотрудник с таким ID не найден.", "warning")
        except IntegrityError:
            db.session.rollback()
            flash("Невозможно удалить сотрудника, поскольку он связан с другими записями. Сначала удалите связанные данные.", "warning")
    else:
        flash("Некорректный ID сотрудника.", "error")
    return redirect(url_for('employees_filter'))


@app.route('/order_action', methods=['POST'])
def order_action():
    action = request.form.get('action', '')

    client_id = request.form.get('client_id', '')
    employee_id = request.form.get('employee_id', '')
    compound = request.form.get('compound', '')
    status = request.form.get('status', '')
    cost = request.form.get('cost', '')

    if not client_id or not employee_id or not compound or not status or not cost:
        flash("Все поля формы должны быть заполнены.", "warning")
        return redirect(url_for('orders_filter'))

    if action == 'add':
        new_order = dbm.Orders(idEm=employee_id, idCl=client_id, compound=compound, status=status, cost=cost)
        try:
            db.session.add(new_order)
            db.session.commit()
        except Exception as e:
            flash("Ошибка при вводе! Проверьте id клиента и сотрудника!", "warning")
            return redirect(url_for('orders_filter'))
        flash("Заказ успешно добавлен!", "success")
        
    elif action == 'update':
        order_id = request.form.get('order_id', None)
        if order_id is None:
            flash("Не указан заказ для обновления.", "warning")
            return redirect(url_for('orders_filter'))
        
        order = dbm.Orders.query.get(order_id)
        if not order:
            flash("Заказ не найден.", "warning")
            return redirect(url_for('orders_filter'))

        order.idCl = client_id
        order.idEm = employee_id
        order.compound = compound
        order.status = status
        order.cost = cost
        db.session.commit()
        flash("Заказ успешно обновлен!", "success")
    
    return redirect(url_for('orders_filter'))



@app.route('/delete_order', methods=['POST'])
def delete_order():
    order_id = request.form.get('id')
    if order_id:
        try:
            order = dbm.Orders.query.get(order_id)
            if order:
                db.session.delete(order)
                db.session.commit()
                flash("Заказ успешно удалён.", "success")
            else:
                flash("Заказ с таким ID не найден.", "warning")
        except IntegrityError:
            db.session.rollback()
            flash("Невозможно удалить заказ, поскольку он связан с другими записями. Сначала удалите связанные данные.", "warning")
    else:
        flash("Некорректный ID заказа.", "error")
    return redirect(url_for('orders_filter'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
