from sqlalchemy import Enum
from .database import db


class Admin(db.Model):
    __tablename__ = 'admins' 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(1024), nullable=False)

    def __repr__(self):
        return f'<Admin {self.username}>'

class Clients(db.Model):
    __tablename__ = 'Clients'
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    surname = db.Column(db.String(255), nullable=False)
    importance = db.Column(Enum('VIP', 'COM'), nullable=False)

class Employees(db.Model):
    __tablename__ = 'Employees'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    surname = db.Column(db.String(255), nullable=False)
    birthday = db.Column(db.Date, nullable=False)
    post = db.Column(db.String(255), nullable=False)

class Orders(db.Model):
    __tablename__ = 'Orders'
    id = db.Column(db.Integer, primary_key=True)
    idEm = db.Column(db.Integer, db.ForeignKey('Employees.id'), nullable=False)
    idCl = db.Column(db.Integer, db.ForeignKey('Clients.id'), nullable=False)
    compound = db.Column(db.Text, nullable=False)
    status = db.Column(Enum('Created', 'Awaiting Payment', 'In Process', 'Ready for Pickup', 'Issued'), nullable=False)
    cost = db.Column(db.Numeric(10, 2), nullable=False)

