# Trading Bot Application

A comprehensive Flask-based trading bot platform with strategy automation, user management, payments integration, and both paper and live trading capabilities.

## Features

### 🚀 Core Functionality

- **Multi-Strategy Trading**: Implement and run multiple trading strategies
- **Paper & Live Trading**: Test strategies with paper trading before going live
- **Real-time Scheduling**: Automated strategy execution every 5 minutes
- **User Management**: Complete authentication and authorization system
- **Payment Integration**: Razorpay integration for subscriptions
- **Audit Logging**: Complete audit trail of all actions

### 📈 Implemented Trading Strategies

1. **Moving Average Crossover**: Simple two-MA crossover with stop-loss/take-profit
2. **Momentum Breakout**: Trade breakouts above X-day high with volume confirmation
3. **RSI Mean Reversion**: Buy when RSI < 30, sell when RSI > 70
4. **VWAP Intraday Scalper**: Trade deviations from VWAP
5. **Bollinger Band Reversal**: Trade reversals at band extremes
6. **More strategies**: Extensible architecture for adding new strategies

### 🔧 Technical Features

- **Real Market Data**: Mock data implementation with structure for real data integration
- **Order Management**: Complete order lifecycle management
- **Risk Controls**: Position sizing and risk management
- **Database Migrations**: Flask-Migrate for database schema management
- **Comprehensive Testing**: Unit tests for core functionality
- **Logging System**: Detailed application logging

## Quick Start

### Prerequisites

- Python 3.8+
- Git

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd application
   ```

2. **Create and activate virtual environment**

   ```bash
   python -m venv venv
   
   # On Windows
   .\venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the project root:

   ```env
   # Flask Configuration
   SECRET_KEY=your-secret-key-here-change-in-production
   DEBUG=True
   FLASK_CONFIG=development

   # Database Configuration
   DATABASE_URL=sqlite:///dev.db

   # Broker API Configuration (Replace with your actual values)
   BROKER_API_KEY=your_broker_api_key_here
   BROKER_API_SECRET=your_broker_api_secret_here

   # Razorpay Configuration (Replace with your actual values)
   RAZORPAY_KEY=your_razorpay_key_here
   RAZORPAY_SECRET=your_razorpay_secret_here

   # Scheduler Configuration
   SCHEDULER_ENABLED=True
   ```

5. **Initialize Database**

   ```bash
   # Set Flask app
   set FLASK_APP=run.py  # Windows
   export FLASK_APP=run.py  # macOS/Linux

   # Initialize migrations
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Create Admin User**

   ```bash
   flask create-admin
   # Follow prompts to create admin account
   ```

7. **Run the Application**

   ```bash
   python run.py
   ```

   The application will be available at `http://127.0.0.1:5000`

## Project Structure

```
application/
├── app/
│   ├── __init__.py              # Application factory
│   ├── config.py               # Configuration settings
│   ├── models.py               # Database models
│   ├── admin/                  # Admin panel routes
│   ├── auth/                   # Authentication routes & forms
│   ├── exchange_adapter/       # Broker API integration
│   ├── orders/                 # Order management
│   ├── payments/               # Payment processing
│   ├── strategies/             # Trading strategies
│   ├── templates/              # HTML templates
│   ├── user/                   # User dashboard routes
│   └── utils/                  # Utility functions
├── migrations/                 # Database migrations
├── tests/                      # Unit tests
├── venv/                       # Virtual environment
├── .env                        # Environment variables
├── requirements.txt            # Python dependencies
├── run.py                      # Application entry point
└── README.md                   # This file
```

## Key Components

### Strategy Engine

Located in `app/strategies/`, the strategy engine provides:

- **Base Strategy Class**: Template for implementing new strategies
- **Strategy Execution**: Automated running of active strategies
- **Signal Generation**: Convert market analysis into trading signals
- **Risk Management**: Built-in position sizing and risk controls

#### Adding New Strategies

1. Create a new class inheriting from `BaseStrategy`
2. Implement the `generate_signals()` method
3. Add to `STRATEGY_MAP` in `top_strategies.py`

### Order Management

The order manager handles:

- **Paper Trading**: Simulated execution with realistic slippage
- **Live Trading**: Integration with broker APIs
- **Order Lifecycle**: From placement to execution
- **Trade Recording**: Complete trade history

### User Management

- **Authentication**: Secure login/registration system
- **Authorization**: Role-based access control
- **Subscriptions**: Free and Pro plan management
- **Audit Logging**: Track all user actions

## API Integration

### Broker Integration

The application is structured to work with broker APIs like Zerodha Kite:

1. **Configure API Keys**: Add your broker's API credentials to `.env`
2. **Implement Connection**: Update `exchange_adapter/kite_adapter.py`
3. **Market Data**: Replace mock data with real market feeds
4. **Order Placement**: Implement actual order placement logic

### Payment Gateway

Razorpay integration for subscription management:

- Configure Razorpay keys in `.env`
- Webhook handling for payment confirmation
- Automatic subscription activation

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

Individual test files:

```bash
pytest tests/test_strategy_engine.py -v
pytest tests/test_order_manager.py -v
```

## Deployment

### Development

```bash
python run.py
```

### Production

Use a production WSGI server like Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

## Configuration

### Environment Variables

- `SECRET_KEY`: Flask secret key for sessions
- `DEBUG`: Enable/disable debug mode
- `DATABASE_URL`: Database connection string
- `BROKER_API_KEY/SECRET`: Broker API credentials
- `RAZORPAY_KEY/SECRET`: Payment gateway credentials
- `SCHEDULER_ENABLED`: Enable/disable strategy automation

### Database Configuration

The application supports multiple database backends:

- **Development**: SQLite (default)
- **Production**: PostgreSQL, MySQL, etc.

## Monitoring & Logging

### Application Logs

- **Development**: Logs to `logs/app_debug.log`
- **Production**: Logs to stdout

### Audit Trail

All user actions are logged in the `audit_logs` table:

- User registration/login
- Order placement
- Strategy activation
- Payment transactions

## Security Considerations

1. **Environment Variables**: Never commit API keys to version control
2. **Password Hashing**: Uses bcrypt for secure password storage
3. **Session Management**: Secure session handling with Flask-Login
4. **Input Validation**: Form validation with WTForms
5. **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

- Create an issue in the GitHub repository
- Check the logs in `logs/` directory for debugging
- Review the test files for usage examples

## Roadmap

### Upcoming Features

- [ ] Real-time market data streaming
- [ ] Advanced charting and visualization
- [ ] Portfolio analytics and reporting
- [ ] Email notifications
- [ ] API endpoints for external access
- [ ] Mobile app integration
- [ ] Advanced risk management tools
- [ ] Machine learning strategies

### Integration Priorities

1. **Zerodha Kite API**: Complete broker integration
2. **Real Market Data**: NSE/BSE live data feeds
3. **Advanced Strategies**: ML-based trading algorithms
4. **Risk Management**: Advanced position and portfolio risk controls
5. **Reporting**: Comprehensive performance analytics - A Flask-based Trading Application

This is a production-grade real and paper trading web application for the Indian stock market, built with Flask, SQLAlchemy, and Jinja2.

## Features

- **User & Admin Roles**: Secure authentication and role-based access control.
- **Subscription Tiers**: Free (paper-trading) and Pro (real-trading) plans.
- **Strategy Engine**: Pluggable architecture for trading strategies.
- **Order Management**: Simulated paper trading and a stubbed adapter for real trading.
- **Admin Dashboard**: Manage users, subscriptions, and view system logs.
- **User Dashboard**: View P&L, manage orders, and control strategies.
- **Secure & Modular**: Built with security best practices and a modular design using Flask Blueprints.

## Tech Stack

- **Backend**: Python 3.11+, Flask
- **Database**: SQLAlchemy ORM (SQLite for dev, configurable for production)
- **Frontend**: Jinja2, Tailwind CSS (via CDN), Vanilla JavaScript
- **Authentication**: Flask-Login, Passlib for password hashing
- **Scheduling**: APScheduler
- **Testing**: Pytest

## Project Setup

### 1. Clone the Repository

\`\`\`bash
git clone <your-repo-url>
cd trading-bot
\`\`\`

### 2. Create a Virtual Environment

It's highly recommended to use a virtual environment to manage project dependencies.

\`\`\`bash
python3 -m venv venv
source venv/bin/activate

# On Windows, use: venv\Scripts\activate

\`\`\`

### 3. Install Dependencies

Install all required packages from `requirements.txt`.

\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 4. Configure Environment Variables

Copy the example environment file and fill in your credentials.

\`\`\`bash
cp .env.example .env
\`\`\`

Now, open the `.env` file and edit the variables:

- `SECRET_KEY`: A long, random string for session security. Generate one with `python -c 'import secrets; print(secrets.token_hex(16))'`.
- `DATABASE_URL`: Defaults to SQLite. For PostgreSQL, use `postgresql://user:password@host:port/dbname`.
- `DEBUG`: Set to `True` for development (enables file logging and debug pages), `False` for production.
- `BROKER_API_KEY`, `BROKER_API_SECRET`: Your trading broker's API credentials.
- `RAZORPAY_KEY`, `RAZORPAY_SECRET`: Your Razorpay API credentials for payments.

### 5. Initialize the Database

Run the Flask-Migrate commands to set up your database schema.

\`\`\`bash
flask db init  # Only run this the very first time
flask db migrate -m "Initial migration."
flask db upgrade
\`\`\`

### 6. Create an Admin User (Optional)

You can create an admin user from the command line to manage the application.

\`\`\`bash
flask create-admin --username <admin_user> --email <admin_email> --password <strong_password>
\`\`\`

## Running the Application

### Development Server

To run the application locally for development:

\`\`\`bash
flask run
\`\`\`

The application will be available at `http://127.0.0.1:5000`.

### Production

For production, use a proper WSGI server like Gunicorn:

\`\`\`bash
gunicorn --workers 4 --bind 0.0.0.0:8000 run:app
\`\`\`

## How It Works

### Broker API Integration

The application is designed to be broker-agnostic. The core logic for connecting to a broker is located in:

`app/exchange_adapter/kite_adapter.py`

You must implement the methods within this file (`connect`, `place_order`, etc.) using your broker's official SDK (e.g., Kite Connect). The methods currently raise `NotImplementedError`.

### Logging

- **DEBUG Mode (`DEBUG=True`)**: Logs are written to `logs/app_debug.log`. This file is rotated to prevent it from growing too large. You can view logs from the Admin Panel at `/admin/logs`.
- **Production Mode (`DEBUG=False`)**: File logging is disabled. Only `WARNING` and `ERROR` level logs are printed to standard output (console).

### Running Tests

To run the unit tests for the project:

\`\`\`bash
pytest
\`\`\`
