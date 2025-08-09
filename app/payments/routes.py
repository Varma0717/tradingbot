from flask import Blueprint, render_template, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
import razorpay
from ..models import Payment
from .. import db

payments = Blueprint('payments', __name__)

@payments.route('/upgrade', methods=['GET', 'POST'])
@login_required
def upgrade():
    """
    Creates a Razorpay order and redirects user to payment.
    """
    if current_user.has_pro_plan:
        flash("You already have a Pro plan.", "info")
        return redirect(url_for('user.dashboard'))

    # TODO: Get amount from a config or database
    amount_in_paise = 99900 # e.g., Rs. 999.00

    client = razorpay.Client(
        auth=(current_app.config['RAZORPAY_KEY'], current_app.config['RAZORPAY_SECRET'])
    )
    
    try:
        order_data = {
            'amount': amount_in_paise,
            'currency': 'INR',
            'receipt': f'receipt_user_{current_user.id}',
            'notes': {
                'user_id': current_user.id,
                'plan': 'pro'
            }
        }
        razorpay_order = client.order.create(data=order_data)
        
        # Create a payment record in our DB
        payment = Payment(
            user_id=current_user.id,
            amount=amount_in_paise / 100,
            razorpay_order_id=razorpay_order['id'],
            status='created'
        )
        db.session.add(payment)
        db.session.commit()

        return render_template('payments/checkout.html', 
                               order=razorpay_order, 
                               razorpay_key=current_app.config['RAZORPAY_KEY'])

    except Exception as e:
        current_app.logger.exception(f"Razorpay order creation failed for user {current_user.id}: {e}")
        flash("Could not connect to payment gateway. Please try again later.", "danger")
        return redirect(url_for('user.billing'))