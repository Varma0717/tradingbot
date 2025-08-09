# Trading Bot - A Flask-based Trading Application

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
