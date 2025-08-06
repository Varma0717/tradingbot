"""
Email Notifier for sending notifications via email.
"""

import asyncio
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from ..utils.logger import get_logger
from .notification_manager import Notification


class EmailNotifier:
    """
    Email notifier for sending notifications via SMTP.
    """

    def __init__(self, config):
        """
        Initialize email notifier.

        Args:
            config: Email configuration object
        """
        self.config = config
        self.logger = get_logger(__name__)

        # SMTP settings
        self.smtp_server = getattr(config, "smtp_server", "smtp.gmail.com")
        self.smtp_port = getattr(config, "smtp_port", 587)
        self.username = getattr(config, "username", "")
        self.password = getattr(config, "password", "")
        self.from_email = getattr(config, "from_email", self.username)
        self.to_emails = getattr(config, "to_emails", [])

        # Email settings
        self.use_tls = getattr(config, "use_tls", True)
        self.use_ssl = getattr(config, "use_ssl", False)
        self.timeout = getattr(config, "timeout", 30)

        # Template settings
        self.subject_prefix = getattr(config, "subject_prefix", "[Trading Bot]")
        self.include_metadata = getattr(config, "include_metadata", True)

    async def send(self, notification: Notification) -> bool:
        """
        Send notification via email.

        Args:
            notification: Notification to send

        Returns:
            True if sent successfully
        """
        try:
            if not self.to_emails:
                self.logger.warning("No recipient emails configured")
                return False

            # Create email message
            msg = self._create_email_message(notification)

            # Send email
            success = await self._send_email(msg)

            if success:
                self.logger.info(f"Email notification sent: {notification.title}")
            else:
                self.logger.error(
                    f"Failed to send email notification: {notification.title}"
                )

            return success

        except Exception as e:
            self.logger.error(f"Error sending email notification: {e}")
            return False

    def _create_email_message(self, notification: Notification) -> MIMEMultipart:
        """
        Create email message from notification.

        Args:
            notification: Notification object

        Returns:
            Email message
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")

            # Set headers
            msg["From"] = self.from_email
            msg["To"] = ", ".join(self.to_emails)
            msg["Subject"] = f"{self.subject_prefix} {notification.title}"

            # Create email body
            html_body = self._create_html_body(notification)
            text_body = self._create_text_body(notification)

            # Add text and HTML parts
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            return msg

        except Exception as e:
            self.logger.error(f"Error creating email message: {e}")
            raise

    def _create_text_body(self, notification: Notification) -> str:
        """Create plain text email body."""
        try:
            body = f"Trading Bot Notification\n"
            body += f"=" * 50 + "\n\n"
            body += f"Type: {notification.type.value.upper()}\n"
            body += f"Time: {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            body += f"Title: {notification.title}\n\n"
            body += f"Message:\n{notification.message}\n\n"

            if self.include_metadata and notification.metadata:
                body += f"Additional Information:\n"
                for key, value in notification.metadata.items():
                    body += f"  {key}: {value}\n"
                body += "\n"

            body += f"Priority: {self._get_priority_text(notification.priority)}\n"
            body += f"Notification ID: {notification.id}\n"

            return body

        except Exception as e:
            self.logger.error(f"Error creating text body: {e}")
            return notification.message

    def _create_html_body(self, notification: Notification) -> str:
        """Create HTML email body."""
        try:
            # Determine colors based on notification type and priority
            type_colors = {
                "info": "#17a2b8",
                "warning": "#ffc107",
                "error": "#dc3545",
                "critical": "#6f42c1",
                "trade": "#28a745",
                "signal": "#007bff",
                "risk": "#fd7e14",
                "system": "#6c757d",
            }

            color = type_colors.get(notification.type.value, "#6c757d")

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Trading Bot Notification</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        background-color: {color};
                        color: white;
                        padding: 20px;
                        border-radius: 5px 5px 0 0;
                        text-align: center;
                    }}
                    .content {{
                        background-color: #f8f9fa;
                        padding: 20px;
                        border: 1px solid #dee2e6;
                    }}
                    .footer {{
                        background-color: #e9ecef;
                        padding: 10px 20px;
                        border-radius: 0 0 5px 5px;
                        border: 1px solid #dee2e6;
                        border-top: none;
                        font-size: 12px;
                        color: #6c757d;
                    }}
                    .badge {{
                        background-color: {color};
                        color: white;
                        padding: 2px 8px;
                        border-radius: 3px;
                        font-size: 12px;
                        font-weight: bold;
                        text-transform: uppercase;
                    }}
                    .metadata {{
                        background-color: white;
                        border: 1px solid #dee2e6;
                        border-radius: 3px;
                        padding: 10px;
                        margin-top: 15px;
                    }}
                    .metadata table {{
                        width: 100%;
                        border-collapse: collapse;
                    }}
                    .metadata td {{
                        padding: 5px 10px;
                        border-bottom: 1px solid #eee;
                    }}
                    .metadata td:first-child {{
                        font-weight: bold;
                        width: 30%;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>🤖 Trading Bot Notification</h2>
                    <span class="badge">{notification.type.value}</span>
                </div>
                
                <div class="content">
                    <h3>{notification.title}</h3>
                    <p><strong>Time:</strong> {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Priority:</strong> {self._get_priority_text(notification.priority)}</p>
                    
                    <div style="margin: 15px 0;">
                        <h4>Message:</h4>
                        <p style="white-space: pre-line;">{notification.message}</p>
                    </div>
            """

            # Add metadata if available
            if self.include_metadata and notification.metadata:
                html += f"""
                    <div class="metadata">
                        <h4>Additional Information:</h4>
                        <table>
                """

                for key, value in notification.metadata.items():
                    html += f"""
                            <tr>
                                <td>{key.replace('_', ' ').title()}:</td>
                                <td>{value}</td>
                            </tr>
                    """

                html += """
                        </table>
                    </div>
                """

            html += f"""
                </div>
                
                <div class="footer">
                    <p>Notification ID: {notification.id}</p>
                    <p>Generated by Crypto Trading Bot</p>
                </div>
            </body>
            </html>
            """

            return html

        except Exception as e:
            self.logger.error(f"Error creating HTML body: {e}")
            return f"<html><body><h3>{notification.title}</h3><p>{notification.message}</p></body></html>"

    def _get_priority_text(self, priority: int) -> str:
        """Get priority text from priority level."""
        priority_map = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}
        return priority_map.get(priority, "Unknown")

    async def _send_email(self, msg: MIMEMultipart) -> bool:
        """
        Send email message via SMTP.

        Args:
            msg: Email message to send

        Returns:
            True if sent successfully
        """
        try:
            # Create SMTP connection
            if self.use_ssl:
                server = smtplib.SMTP_SSL(
                    self.smtp_server, self.smtp_port, timeout=self.timeout
                )
            else:
                server = smtplib.SMTP(
                    self.smtp_server, self.smtp_port, timeout=self.timeout
                )
                if self.use_tls:
                    server.starttls()

            # Login if credentials provided
            if self.username and self.password:
                server.login(self.username, self.password)

            # Send email
            server.send_message(msg)
            server.quit()

            return True

        except smtplib.SMTPException as e:
            self.logger.error(f"SMTP error sending email: {e}")
            return False

        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
            return False

    async def is_available(self) -> bool:
        """
        Check if email notifier is available.

        Returns:
            True if available
        """
        try:
            if not self.to_emails:
                return False

            if not self.smtp_server or not self.username:
                return False

            # Test SMTP connection
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=5)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=5)
                if self.use_tls:
                    server.starttls()

            server.quit()
            return True

        except Exception as e:
            self.logger.debug(f"Email notifier not available: {e}")
            return False

    async def close(self):
        """Close email notifier."""
        # No persistent connections to close
        pass

    def __str__(self) -> str:
        """String representation of email notifier."""
        return f"EmailNotifier(server={self.smtp_server}, recipients={len(self.to_emails)})"
