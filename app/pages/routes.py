from flask import Blueprint, render_template, request, flash, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from .. import limiter
import logging

pages = Blueprint("pages", __name__)


@pages.route("/about")
def about():
    """About page with company information and team details."""
    return render_template("pages/about.html", title="About Us")


@pages.route("/services")
def services():
    """Services page showcasing trading services and pricing."""
    return render_template("pages/services.html", title="Services")


@pages.route("/contact", methods=["GET", "POST"])
@limiter.limit("5/minute")  # Limit contact form submissions
def contact():
    """Contact page with contact information and contact form."""
    if request.method == "POST":
        # Handle contact form submission
        try:
            # Check for honeypot field
            if request.form.get("website"):
                # Bot detected, log and ignore
                logging.warning(
                    f"Bot detected in contact form from IP: {request.remote_addr}"
                )
                return jsonify({"success": False, "message": "Invalid submission"}), 403

            # Get form data
            first_name = request.form.get("firstName", "").strip()
            last_name = request.form.get("lastName", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()
            subject = request.form.get("subject", "").strip()
            message = request.form.get("message", "").strip()

            # Basic validation
            if not all([first_name, last_name, email, subject, message]):
                flash("All required fields must be filled out.", "danger")
                return render_template("pages/contact.html", title="Contact Us")

            # In a real application, you would:
            # 1. Save to database
            # 2. Send notification email to admin
            # 3. Send confirmation email to user
            # 4. Integrate with CRM system

            # For now, just log the submission
            logging.info(
                f"Contact form submission: {first_name} {last_name} ({email}) - {subject}"
            )

            flash(
                "Thank you for your message! We'll get back to you within 24 hours.",
                "success",
            )

        except Exception as e:
            logging.error(f"Error processing contact form: {str(e)}")
            flash(
                "There was an error processing your message. Please try again.",
                "danger",
            )

    return render_template("pages/contact.html", title="Contact Us")


@pages.route("/privacy")
def privacy():
    """Privacy policy page."""
    return render_template("pages/privacy.html", title="Privacy Policy")


@pages.route("/terms")
def terms():
    """Terms of service page."""
    return render_template("pages/terms.html", title="Terms of Service")


@pages.route("/sitemap")
def sitemap():
    """Generate XML sitemap for SEO."""
    from flask import Response, url_for

    # In a real application, you would generate this dynamically
    sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>{}</loc>
            <lastmod>2025-08-09</lastmod>
            <changefreq>weekly</changefreq>
            <priority>1.0</priority>
        </url>
        <url>
            <loc>{}</loc>
            <lastmod>2025-08-09</lastmod>
            <changefreq>monthly</changefreq>
            <priority>0.8</priority>
        </url>
        <url>
            <loc>{}</loc>
            <lastmod>2025-08-09</lastmod>
            <changefreq>monthly</changefreq>
            <priority>0.8</priority>
        </url>
        <url>
            <loc>{}</loc>
            <lastmod>2025-08-09</lastmod>
            <changefreq>monthly</changefreq>
            <priority>0.6</priority>
        </url>
    </urlset>""".format(
        url_for("index", _external=True),
        url_for("pages.about", _external=True),
        url_for("pages.services", _external=True),
        url_for("pages.contact", _external=True),
    )

    return Response(sitemap_xml, mimetype="application/xml")
