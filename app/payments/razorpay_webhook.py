from flask import Blueprint, request, abort, current_app
import razorpay
import hmac
import hashlib
from ..models import Payment, Subscription, User
from .. import db

webhook = Blueprint('webhook', __name__)

@webhook.route('/razorpay', methods=['POST'])
def razorpay_webhook():
    """
    Handles incoming webhooks from Razorpay to confirm payments.
    """
    webhook_secret = current_app.config.get('RAZORPAY_WEBHOOK_SECRET')
    # TODO: You must set a webhook secret in your Razorpay dashboard and .env file
    # if not webhook_secret:
    #     current_app.logger.error("RAZORPAY_WEBHOOK_SECRET is not set.")
    #     abort(500)

    payload = request.get_data(as_text=True)
    received_signature = request.headers.get('X-Razorpay-Signature')

    # 1. Verify the signature (placeholder for now)
    # try:
    #     client = razorpay.Client(auth=(current_app.config['RAZORPAY_KEY'], current_app.config['RAZORPAY_SECRET']))
    #     client.utility.verify_webhook_signature(payload, received_signature, webhook_secret)
    # except razorpay.errors.SignatureVerificationError as e:
    #     current_app.logger.warning(f"Razorpay signature verification failed: {e}")
    #     abort(400)

    data = request.json
    event = data.get('event')

    if event == 'payment.captured':
        payment_entity = data['payload']['payment']['entity']
        order_id = payment_entity['order_id']
        
        payment = Payment.query.filter_by(razorpay_order_id=order_id).first()
        if not payment:
            current_app.logger.error(f"Received webhook for unknown order_id: {order_id}")
            return 'OK', 200

        # 2. Update payment status
        payment.status = 'captured'
        payment.razorpay_payment_id = payment_entity['id']
        
        # 3. Grant subscription access
        user = User.query.get(payment.user_id)
        if user:
            if user.subscription:
                user.subscription.plan = 'pro'
                user.subscription.status = 'active'
                # TODO: Extend end_date if already subscribed
            else:
                new_sub = Subscription(user_id=user.id, plan='pro', status='active')
                db.session.add(new_sub)
            
            current_app.logger.info(f"User {user.id} successfully upgraded to Pro plan via webhook.")
        
        db.session.commit()

    return 'OK', 200