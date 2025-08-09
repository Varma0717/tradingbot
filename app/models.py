from datetime import datetime, timedelta
from passlib.hash import bcrypt
from flask_login import UserMixin
from . import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user', nullable=False) # 'user' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    subscription = db.relationship('Subscription', backref='user', uselist=False, cascade="all, delete-orphan")
    orders = db.relationship('Order', backref='user', lazy='dynamic')
    strategies = db.relationship('Strategy', backref='user', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = bcrypt.hash(password)

    def check_password(self, password):
        return bcrypt.verify(password, self.password_hash)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def has_pro_plan(self):
        return self.subscription and self.subscription.plan == 'pro' and self.subscription.is_active

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    plan = db.Column(db.String(20), default='free', nullable=False) # 'free' or 'pro'
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active', nullable=False) # 'active', 'expired', 'cancelled'

    @property
    def is_active(self):
        return self.status == 'active' and (self.end_date is None or self.end_date > datetime.utcnow())

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    strategy_id = db.Column(db.Integer, db.ForeignKey('strategies.id'), nullable=True)
    symbol = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    order_type = db.Column(db.String(20), nullable=False) # 'market', 'limit'
    side = db.Column(db.String(10), nullable=False) # 'buy', 'sell'
    status = db.Column(db.String(20), default='pending', nullable=False) # 'pending', 'filled', 'partial', 'cancelled', 'failed'
    price = db.Column(db.Float, nullable=True) # For limit orders
    filled_price = db.Column(db.Float, nullable=True)
    filled_quantity = db.Column(db.Integer, default=0)
    is_paper = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    trades = db.relationship('Trade', backref='order', cascade="all, delete-orphan")

class Trade(db.Model):
    __tablename__ = 'trades'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    side = db.Column(db.String(10), nullable=False)
    fees = db.Column(db.Float, default=0.0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Strategy(db.Model):
    __tablename__ = 'strategies'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    parameters = db.Column(db.JSON, nullable=True)
    is_active = db.Column(db.Boolean, default=False, nullable=False)

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='INR', nullable=False)
    razorpay_payment_id = db.Column(db.String(100), unique=True, nullable=True)
    razorpay_order_id = db.Column(db.String(100), unique=True, nullable=True)
    status = db.Column(db.String(20), default='created', nullable=False) # 'created', 'captured', 'failed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Can be null for system actions
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.JSON, nullable=True)