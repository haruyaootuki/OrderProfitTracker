from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to orders
    orders = db.relationship('Order', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set user password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(100), unique=True, nullable=False, index=True)
    customer_name = db.Column(db.String(200), nullable=False)
    project_name = db.Column(db.String(200), nullable=False)
    order_amount = db.Column(db.Numeric(15, 2), nullable=False)
    order_date = db.Column(db.Date, nullable=False)
    delivery_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='受注')
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key to user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<Order {self.order_number}>'
    
    def to_dict(self):
        """Convert order to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'order_number': self.order_number,
            'customer_name': self.customer_name,
            'project_name': self.project_name,
            'order_amount': float(self.order_amount),
            'order_date': self.order_date.strftime('%Y-%m-%d') if self.order_date else None,
            'delivery_date': self.delivery_date.strftime('%Y-%m-%d') if self.delivery_date else None,
            'status': self.status,
            'remarks': self.remarks,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class CostData(db.Model):
    __tablename__ = 'cost_data'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    employee_cost = db.Column(db.Numeric(15, 2), nullable=False, default=0)
    bp_cost = db.Column(db.Numeric(15, 2), nullable=False, default=0)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='cost_data')
    
    def __repr__(self):
        return f'<CostData {self.user_id} {self.period_start}-{self.period_end}>'
