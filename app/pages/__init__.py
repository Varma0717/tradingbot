from flask import Blueprint, render_template

pages = Blueprint("pages", __name__)


@pages.route("/about")
def about():
    """About page with company information and team details."""
    return render_template("pages/about.html", title="About Us")


@pages.route("/services")
def services():
    """Services page showcasing trading services and pricing."""
    return render_template("pages/services.html", title="Services")


@pages.route("/contact")
def contact():
    """Contact page with contact information and contact form."""
    return render_template("pages/contact.html", title="Contact Us")
