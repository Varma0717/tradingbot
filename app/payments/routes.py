from flask import Blueprint, render_template, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
import razorpay
from ..models import Payment, Subscription
from .. import db
from datetime import datetime, timedelta

payments = Blueprint("payments", __name__)

# Configuration for different plan prices
PLAN_PRICES = {
    "pro": 99900,  # Rs. 999.00 in paise
    "premium": 199900,  # Rs. 1999.00 in paise
}


@payments.route("/upgrade")
@payments.route("/upgrade/<plan>")
@login_required
def upgrade(plan="pro"):
    """
    Display upgrade options or process upgrade for specific plan.
    """
    if current_user.has_pro_plan:
        flash("You already have an active Pro plan.", "info")
        return redirect(url_for("user.dashboard"))

    if plan not in PLAN_PRICES:
        flash("Invalid plan selected.", "danger")
        return redirect(url_for("user.billing"))

    amount_in_paise = PLAN_PRICES[plan]

    # Check if Razorpay is configured
    if not current_app.config.get("RAZORPAY_KEY") or not current_app.config.get(
        "RAZORPAY_SECRET"
    ):
        flash("Payment gateway is not configured. Please contact support.", "danger")
        return redirect(url_for("user.billing"))

    client = razorpay.Client(
        auth=(current_app.config["RAZORPAY_KEY"], current_app.config["RAZORPAY_SECRET"])
    )

    try:
        order_data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": f'receipt_user_{current_user.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            "notes": {
                "user_id": current_user.id,
                "plan": plan,
                "user_email": current_user.email,
            },
        }
        razorpay_order = client.order.create(data=order_data)

        # Create a payment record in our DB
        payment = Payment(
            user_id=current_user.id,
            amount=amount_in_paise / 100,
            razorpay_order_id=razorpay_order["id"],
            status="created",
        )
        db.session.add(payment)
        db.session.commit()

        return render_template(
            "payments/checkout.html",
            order=razorpay_order,
            plan=plan,
            amount=amount_in_paise / 100,
            razorpay_key=current_app.config["RAZORPAY_KEY"],
        )

    except Exception as e:
        current_app.logger.exception(
            f"Razorpay order creation failed for user {current_user.id}: {e}"
        )
        flash("Could not connect to payment gateway. Please try again later.", "danger")
        return redirect(url_for("user.billing"))


@payments.route("/success")
@login_required
def payment_success():
    """
    Handle successful payment redirect.
    """
    flash("Payment successful! Your subscription has been activated.", "success")
    return redirect(url_for("user.dashboard"))


@payments.route("/cancel")
@login_required
def payment_cancel():
    """
    Handle cancelled payment.
    """
    flash("Payment was cancelled. You can try again anytime.", "info")
    return redirect(url_for("user.billing"))
