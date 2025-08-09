from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from ..models import Order, Trade, Strategy
from ..orders.manager import place_order
from .. import db

user = Blueprint('user', __name__)

@user.before_request
@login_required
def before_request():
    """Protect all user routes."""
    pass

@user.route('/dashboard')
def dashboard():
    # Placeholder data
    pnl_summary = {'daily': 1500.50, 'monthly': 12500.75, 'total': 75000.00}
    balance = 500000.00 # Simulated balance
    active_positions = [
        {'symbol': 'RELIANCE', 'qty': 10, 'avg_price': 2450.00, 'ltp': 2465.00},
        {'symbol': 'TCS', 'qty': 20, 'avg_price': 3300.00, 'ltp': 3280.00},
    ]
    last_10_trades = Trade.query.filter_by(user_id=current_user.id).order_by(Trade.timestamp.desc()).limit(10).all()
    
    return render_template('user/dashboard.html', title='Dashboard', pnl=pnl_summary, balance=balance, positions=active_positions, trades=last_10_trades)

@user.route('/trade', methods=['POST'])
def execute_trade():
    symbol = request.form.get('symbol')
    quantity = int(request.form.get('quantity'))
    order_type = request.form.get('order_type')
    side = request.form.get('side')
    is_paper_str = request.form.get('trade_mode', 'paper')
    is_paper = is_paper_str == 'paper'

    if not symbol or not quantity or not order_type or not side:
        flash('All fields are required for a trade.', 'danger')
        return redirect(url_for('user.dashboard'))

    # Subscription check for real trades
    if not is_paper and not current_user.has_pro_plan:
        flash('You need a Pro plan to place real trades.', 'warning')
        return redirect(url_for('user.dashboard'))

    order_payload = {
        'symbol': symbol.upper(),
        'quantity': quantity,
        'order_type': order_type,
        'side': side,
        'is_paper': is_paper
    }

    try:
        order = place_order(current_user, order_payload)
        flash(f"Order placed successfully! Order ID: {order.id}", 'success')
    except Exception as e:
        flash(f"Failed to place order: {e}", 'danger')

    return redirect(url_for('user.dashboard'))

@user.route('/orders')
def orders():
    active_orders = Order.query.filter(
        Order.user_id == current_user.id, 
        Order.status.in_(['pending', 'partial'])
    ).order_by(Order.created_at.desc()).all()
    
    order_history = Order.query.filter(
        Order.user_id == current_user.id, 
        Order.status.in_(['filled', 'cancelled', 'failed'])
    ).order_by(Order.created_at.desc()).limit(50).all()

    return render_template('user/orders.html', title='Orders', active_orders=active_orders, order_history=order_history)

@user.route('/strategies')
def strategies():
    user_strategies = Strategy.query.filter_by(user_id=current_user.id).all()
    return render_template('user/strategies.html', title='Strategies', strategies=user_strategies)

@user.route('/billing')
def billing():
    return render_template('user/billing.html', title='Subscriptions & Billing')