import os
import click
from flask import g
from app import create_app, db
from app.models import User, UserPreferences
from flask_login import current_user

# Create the Flask app instance from the app factory
app = create_app(os.getenv("FLASK_CONFIG") or "default")


@app.shell_context_processor
def make_shell_context():
    """Makes additional variables available in the Flask shell."""
    return dict(db=db, User=User)


@app.cli.command("create-admin")
@click.option("--username", prompt=True, help="The username for the admin.")
@click.option("--email", prompt=True, help="The email for the admin.")
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="The password for the admin.",
)
def create_admin(username, email, password):
    """Creates a new admin user."""
    if User.query.filter_by(email=email).first():
        print(f"Error: Email {email} already exists.")
        return
    if User.query.filter_by(username=username).first():
        print(f"Error: Username {username} already exists.")
        return

    admin = User(username=username, email=email, role="admin")
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    print(f"Admin user {username} created successfully.")


@app.before_request
def set_trading_mode_global():
    if current_user.is_authenticated:
        preferences = UserPreferences.query.filter_by(user_id=current_user.id).first()
        if not preferences:
            preferences = UserPreferences(
                user_id=current_user.id, trading_mode="paper", theme="dark"
            )
            db.session.add(preferences)
            db.session.commit()
        g.trading_mode = preferences.trading_mode
        g.user_preferences = preferences


if __name__ == "__main__":
    app.run()
