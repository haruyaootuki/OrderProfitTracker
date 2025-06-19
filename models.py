from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Date
from app import Base # Import Base directly

class User(UserMixin, Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Hash and set user password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    customer_name = Column(String(255), nullable=False)
    project_name = Column(String(255), nullable=False)
    sales_amount = Column(Numeric(10, 2), nullable=False, default=0)
    order_amount = Column(Numeric(10, 2), nullable=False, default=0)
    invoiced_amount = Column(Numeric(10, 2), nullable=False, default=0)
    order_date = Column(Date, nullable=False)
    contract_type = Column(String(16))
    sales_stage = Column(String(16))
    billing_month = Column(Date)
    work_in_progress = Column(Boolean, default=False)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Order {self.project_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'project_name': self.project_name,
            'sales_amount': float(self.sales_amount),
            'order_amount': float(self.order_amount),
            'invoiced_amount': float(self.invoiced_amount),
            'order_date': self.order_date.strftime('%Y-%m-%d') if self.order_date else None,
            'contract_type': self.contract_type,
            'sales_stage': self.sales_stage,
            'billing_month': self.billing_month.strftime('%Y-%m-%d') if self.billing_month else None,
            'work_in_progress': self.work_in_progress,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
