import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, "..", ".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "a-very-hard-to-guess-string"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "t")

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

    # Rate limiting
    RATELIMIT_STORAGE_URL = "memory://"  # In production, use Redis
    RATELIMIT_DEFAULT = "100/hour"

    # Security headers
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year for static files

    # Session security
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours

    # Email configuration
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ["true", "on", "1"]
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")

    # Broker and Payment API Keys
    BROKER_API_KEY = os.environ.get("BROKER_API_KEY")
    BROKER_API_SECRET = os.environ.get("BROKER_API_SECRET")

    # Binance API Keys for Crypto Trading
    BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY")
    BINANCE_API_SECRET = os.environ.get("BINANCE_API_SECRET")
    BINANCE_TESTNET = os.environ.get("BINANCE_TESTNET", "true").lower() in [
        "true",
        "on",
        "1",
    ]

    RAZORPAY_KEY = os.environ.get("RAZORPAY_KEY")
    RAZORPAY_SECRET = os.environ.get("RAZORPAY_SECRET")

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    # MySQL configuration for XAMPP
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "trademantra")

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    # Production-specific security settings
    SESSION_COOKIE_SECURE = True  # Require HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Enhanced CSRF protection for production
    WTF_CSRF_SSL_STRICT = True

    # Rate limiting with Redis in production
    RATELIMIT_STORAGE_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SCHEDULER_ENABLED = False  # Disable scheduler in tests


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
