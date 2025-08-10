from datetime import datetime, timedelta
from passlib.hash import bcrypt
from flask_login import UserMixin
from . import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default="user", nullable=False)  # 'user' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    subscription = db.relationship(
        "Subscription", backref="user", uselist=False, cascade="all, delete-orphan"
    )
    preferences = db.relationship(
        "UserPreferences", backref="user", uselist=False, cascade="all, delete-orphan"
    )
    orders = db.relationship("Order", backref="user", lazy="dynamic")
    strategies = db.relationship("Strategy", backref="user", lazy="dynamic")
    audit_logs = db.relationship("AuditLog", backref="user", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = bcrypt.hash(password)

    def check_password(self, password):
        return bcrypt.verify(password, self.password_hash)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def has_pro_plan(self):
        return (
            self.subscription
            and self.subscription.plan == "pro"
            and self.subscription.is_active
        )


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class UserPreferences(db.Model):
    __tablename__ = "user_preferences"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True
    )
    trading_mode = db.Column(
        db.String(10), default="paper", nullable=False
    )  # 'paper' or 'live'
    default_exchange_type = db.Column(
        db.String(10), default="stocks", nullable=False
    )  # 'stocks' or 'crypto'
    risk_level = db.Column(
        db.String(10), default="medium", nullable=False
    )  # 'low', 'medium', 'high'
    max_position_size = db.Column(db.Float, default=10000.0)  # Max amount per trade
    daily_loss_limit = db.Column(db.Float, default=5000.0)  # Daily stop loss
    notifications_enabled = db.Column(db.Boolean, default=True)
    email_alerts = db.Column(db.Boolean, default=True)
    sms_alerts = db.Column(db.Boolean, default=False)
    theme = db.Column(
        db.String(10), default="dark", nullable=False
    )  # 'light' or 'dark'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    @property
    def is_live_trading(self):
        return self.trading_mode == "live"

    @property
    def is_paper_trading(self):
        return self.trading_mode == "paper"


class Subscription(db.Model):
    __tablename__ = "subscriptions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True
    )
    plan = db.Column(db.String(20), default="free", nullable=False)  # 'free' or 'pro'
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    status = db.Column(
        db.String(20), default="active", nullable=False
    )  # 'active', 'expired', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_active(self):
        return self.status == "active" and (
            self.end_date is None or self.end_date > datetime.utcnow()
        )


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    strategy_id = db.Column(db.Integer, db.ForeignKey("strategies.id"), nullable=True)
    symbol = db.Column(db.String(20), nullable=False)
    exchange_type = db.Column(
        db.String(10), default="stocks", nullable=False
    )  # 'stocks' or 'crypto'
    quantity = db.Column(
        db.Float, nullable=False
    )  # Changed to Float for crypto decimals
    order_type = db.Column(db.String(20), nullable=False)  # 'market', 'limit'
    side = db.Column(db.String(10), nullable=False)  # 'buy', 'sell'
    status = db.Column(
        db.String(20), default="pending", nullable=False
    )  # 'pending', 'filled', 'partial', 'cancelled', 'failed'
    price = db.Column(db.Float, nullable=True)  # For limit orders
    filled_price = db.Column(db.Float, nullable=True)
    filled_quantity = db.Column(
        db.Float, default=0
    )  # Changed to Float for crypto decimals
    exchange_order_id = db.Column(db.String(100), nullable=True)  # Broker's order ID
    error_message = db.Column(db.Text, nullable=True)  # Error details if order fails
    is_paper = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    trades = db.relationship("Trade", backref="order", cascade="all, delete-orphan")


class Trade(db.Model):
    __tablename__ = "trades"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    exchange_type = db.Column(
        db.String(10), default="stocks", nullable=False
    )  # 'stocks' or 'crypto'
    quantity = db.Column(
        db.Float, nullable=False
    )  # Changed to Float for crypto decimals
    price = db.Column(db.Float, nullable=False)
    side = db.Column(db.String(10), nullable=False)
    fees = db.Column(db.Float, default=0.0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Strategy(db.Model):
    __tablename__ = "strategies"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    parameters = db.Column(db.JSON, nullable=True)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(
        db.String(20), default="pending", nullable=False
    )  # 'pending', 'approved', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Payment(db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default="INR", nullable=False)
    razorpay_payment_id = db.Column(db.String(100), unique=True, nullable=True)
    razorpay_order_id = db.Column(db.String(100), unique=True, nullable=True)
    status = db.Column(
        db.String(20), default="created", nullable=False
    )  # 'created', 'captured', 'failed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ExchangeConnection(db.Model):
    __tablename__ = "exchange_connections"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    exchange_name = db.Column(
        db.String(50), nullable=False
    )  # 'zerodha', 'upstox', etc.
    api_key = db.Column(db.String(255), nullable=True)  # Encrypted
    api_secret = db.Column(db.String(255), nullable=True)  # Encrypted
    access_token = db.Column(db.String(255), nullable=True)  # Encrypted
    status = db.Column(
        db.String(20), default="disconnected", nullable=False
    )  # 'connected', 'disconnected', 'error'
    last_connected = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = db.relationship("User", backref="exchange_connections")

    @property
    def is_connected(self):
        return self.status == "connected"

    def get_display_name(self):
        """Get user-friendly display name for the exchange"""
        display_names = {
            "zerodha": "Zerodha Kite",
            "upstox": "Upstox",
            "angelbroking": "Angel Broking",
            "iifl": "IIFL Securities",
            "fyers": "Fyers",
            "aliceblue": "Alice Blue",
            "binance": "Binance (Crypto)",
            "binance_testnet": "Binance Testnet (Crypto)",
        }
        return display_names.get(self.exchange_name, self.exchange_name.title())


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )  # Can be null for system actions
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.JSON, nullable=True)


class TradingBotStatus(db.Model):
    __tablename__ = "trading_bot_status"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True
    )
    is_running = db.Column(db.Boolean, default=False, nullable=False)
    bot_type = db.Column(
        db.String(20), default="stock", nullable=False
    )  # 'stock' or 'crypto'
    strategies = db.Column(db.JSON, nullable=True)  # List of active strategies
    started_at = db.Column(db.DateTime, nullable=True)
    stopped_at = db.Column(db.DateTime, nullable=True)
    total_trades = db.Column(db.Integer, default=0)
    daily_pnl = db.Column(db.Float, default=0.0)
    win_rate = db.Column(db.Float, default=0.0)
    open_positions = db.Column(db.Integer, default=0)
    strategies_active = db.Column(db.Integer, default=0)
    last_heartbeat = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = db.relationship("User", backref="trading_bot_status")

    @property
    def is_active(self):
        """Check if bot is considered active (recent heartbeat)"""
        if not self.is_running or not self.last_heartbeat:
            return False
        # Consider bot active if heartbeat is within last 5 minutes
        return (datetime.utcnow() - self.last_heartbeat).total_seconds() < 300
