from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
)
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from .forms import LoginForm, RegistrationForm
from ..models import User, AuditLog
from .. import db, limiter, mail
import secrets
from datetime import datetime, timedelta

auth = Blueprint("auth", __name__)


def send_verification_email(user, token):
    """
    Send email verification email.
    """
    try:
        msg = Message(
            subject="Verify Your TradingBot Account",
            recipients=[user.email],
            sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
        )

        verification_url = url_for("auth.verify_email", token=token, _external=True)

        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Verify Your Email</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #2563eb;">TradingBot</h1>
                </div>
                
                <h2>Welcome to TradingBot!</h2>
                
                <p>Hi {user.username},</p>
                
                <p>Thank you for registering with TradingBot. To complete your registration and start trading, please verify your email address by clicking the button below:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background-color: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        Verify Email Address
                    </a>
                </div>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #666;">{verification_url}</p>
                
                <p>This verification link will expire in 24 hours.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                
                <p style="color: #666; font-size: 14px;">
                    If you didn't create an account with TradingBot, please ignore this email.
                </p>
                
                <p style="color: #666; font-size: 14px;">
                    Best regards,<br>
                    The TradingBot Team
                </p>
            </div>
        </body>
        </html>
        """

        mail.send(msg)
        current_app.logger.info(f"Verification email sent to {user.email}")
        return True

    except Exception as e:
        current_app.logger.error(
            f"Failed to send verification email to {user.email}: {str(e)}"
        )
        # Fallback: log the verification URL for development
        verification_url = url_for("auth.verify_email", token=token, _external=True)
        current_app.logger.info(
            f"Email verification URL for {user.email}: {verification_url}"
        )
        return False


@auth.route("/register", methods=["GET", "POST"])
@limiter.limit("5/minute")  # Limit registration attempts
def register():
    if current_user.is_authenticated:
        return redirect(url_for("user.dashboard"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        # Generate verification token and send email
        verification_token = secrets.token_urlsafe(32)

        # Store verification token (in production, you'd add this to User model)
        # For now, just log the verification URL
        send_verification_email(user, verification_token)

        # Log the registration
        log = AuditLog(
            action="user_registered",
            user_id=user.id,
            details={"email": user.email, "username": user.username},
        )
        db.session.add(log)
        db.session.commit()

        flash(
            "Congratulations, you are now registered! Check your email for verification link.",
            "success",
        )
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", title="Register", form=form)


@auth.route("/verify-email/<token>")
def verify_email(token):
    """
    Verify email address using token.
    TODO: Implement token validation and user email verification.
    """
    flash(
        "Email verification is not yet implemented. You can proceed to login.", "info"
    )
    return redirect(url_for("auth.login"))


@auth.route("/login", methods=["GET", "POST"])
@limiter.limit("10/minute")  # Limit login attempts
def login():
    if current_user.is_authenticated:
        return redirect(url_for("user.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or not next_page.startswith("/"):
            next_page = url_for("user.dashboard")
        flash("You have been logged in successfully.", "success")
        return redirect(next_page)
    return render_template("auth/login.html", title="Sign In", form=form)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))
