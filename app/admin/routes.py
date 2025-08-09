import os
from flask import Blueprint, render_template, current_app, abort, flash, redirect, url_for
from flask_login import login_required
from ..utils.helpers import admin_required
from ..models import User, Subscription, Payment, AuditLog
from .. import db

admin = Blueprint('admin', __name__)

@admin.before_request
@login_required
@admin_required
def before_request():
    """Protect all admin routes."""
    pass

@admin.route('/')
def dashboard():
    user_count = User.query.count()
    pro_subscriptions = Subscription.query.filter_by(plan='pro', status='active').count()
    total_payments = db.session.query(db.func.sum(Payment.amount)).filter(Payment.status == 'captured').scalar() or 0
    return render_template('admin/dashboard.html', title='Admin Dashboard', user_count=user_count, pro_subscriptions=pro_subscriptions, total_payments=total_payments)

@admin.route('/users')
def manage_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', title='Manage Users', users=users)

@admin.route('/user/<int:user_id>/toggle_plan')
def toggle_user_plan(user_id):
    user = User.query.get_or_404(user_id)
    # This is a simplified toggle. A real app would have more logic.
    if user.subscription:
        if user.subscription.plan == 'pro':
            user.subscription.plan = 'free'
            flash(f"User {user.username} downgraded to Free plan.", "info")
        else:
            user.subscription.plan = 'pro'
            flash(f"User {user.username} upgraded to Pro plan.", "info")
    else:
        # Create a new subscription if none exists
        new_sub = Subscription(user_id=user.id, plan='pro', status='active')
        db.session.add(new_sub)
        flash(f"User {user.username} upgraded to Pro plan.", "info")
    
    db.session.commit()
    return redirect(url_for('admin.manage_users'))


@admin.route('/logs')
def view_logs():
    if not current_app.config['DEBUG']:
        abort(404) # This page is only available in debug mode

    log_file_path = os.path.join(current_app.root_path, '..', 'logs', 'app_debug.log')
    try:
        with open(log_file_path, 'r') as f:
            # Read last 100 lines
            log_lines = f.readlines()[-100:]
            log_content = "".join(reversed(log_lines))
    except FileNotFoundError:
        log_content = "Log file not found."
    
    return render_template('admin/logs.html', title='System Logs', log_content=log_content)

@admin.route('/audit_trail')
def audit_trail():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(200).all()
    return render_template('admin/audit_trail.html', title='Audit Trail', logs=logs)