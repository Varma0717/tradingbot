"""
Telegram Notifier for sending notifications via Telegram Bot API.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

try:
    import aiohttp
except ImportError:
    aiohttp = None

from ..utils.logger import get_logger
from .notification_manager import Notification


class TelegramNotifier:
    """
    Telegram notifier for sending notifications via Telegram Bot API.
    """

    def __init__(self, config):
        """
        Initialize Telegram notifier.

        Args:
            config: Telegram configuration object
        """
        self.config = config
        self.logger = get_logger(__name__)

        # Telegram settings
        self.bot_token = getattr(config, "bot_token", "")
        self.chat_ids = getattr(config, "chat_ids", [])
        self.parse_mode = getattr(config, "parse_mode", "HTML")
        self.timeout = getattr(config, "timeout", 30)

        # API settings
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"

        # Message formatting
        self.include_metadata = getattr(config, "include_metadata", True)
        self.max_message_length = 4096  # Telegram limit

        # Check if aiohttp is available
        if aiohttp is None:
            self.logger.warning(
                "aiohttp not available - Telegram notifications will not work"
            )

    async def send(self, notification: Notification) -> bool:
        """
        Send notification via Telegram.

        Args:
            notification: Notification to send

        Returns:
            True if sent successfully
        """
        try:
            if aiohttp is None:
                self.logger.error("aiohttp not available for Telegram notifications")
                return False

            if not self.chat_ids:
                self.logger.warning("No Telegram chat IDs configured")
                return False

            # Create message
            message = self._create_message(notification)

            # Send to all chat IDs
            success = True
            for chat_id in self.chat_ids:
                result = await self._send_message(chat_id, message)
                if not result:
                    success = False

            if success:
                self.logger.info(f"Telegram notification sent: {notification.title}")
            else:
                self.logger.error(
                    f"Failed to send Telegram notification: {notification.title}"
                )

            return success

        except Exception as e:
            self.logger.error(f"Error sending Telegram notification: {e}")
            return False

    def _create_message(self, notification: Notification) -> str:
        """
        Create Telegram message from notification.

        Args:
            notification: Notification object

        Returns:
            Formatted message
        """
        try:
            # Emoji mapping for notification types
            emoji_map = {
                "info": "ℹ️",
                "warning": "⚠️",
                "error": "❌",
                "critical": "🚨",
                "trade": "💰",
                "signal": "📊",
                "risk": "⚡",
                "system": "🤖",
            }

            emoji = emoji_map.get(notification.type.value, "📢")

            if self.parse_mode == "HTML":
                message = self._create_html_message(notification, emoji)
            elif self.parse_mode == "Markdown":
                message = self._create_markdown_message(notification, emoji)
            else:
                message = self._create_plain_message(notification, emoji)

            # Truncate if too long
            if len(message) > self.max_message_length:
                message = (
                    message[: self.max_message_length - 100]
                    + "\n\n... (message truncated)"
                )

            return message

        except Exception as e:
            self.logger.error(f"Error creating Telegram message: {e}")
            return f"{notification.title}\n\n{notification.message}"

    def _create_html_message(self, notification: Notification, emoji: str) -> str:
        """Create HTML formatted message."""
        try:
            message = f"{emoji} <b>{notification.title}</b>\n\n"
            message += f"<b>Type:</b> {notification.type.value.upper()}\n"
            message += (
                f"<b>Time:</b> {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            message += (
                f"<b>Priority:</b> {self._get_priority_text(notification.priority)}\n\n"
            )

            # Add message content
            message += f"<b>Message:</b>\n{self._escape_html(notification.message)}\n\n"

            # Add metadata if available
            if self.include_metadata and notification.metadata:
                message += f"<b>Details:</b>\n"
                for key, value in notification.metadata.items():
                    key_formatted = key.replace("_", " ").title()
                    message += (
                        f"• <b>{key_formatted}:</b> {self._escape_html(str(value))}\n"
                    )
                message += "\n"

            message += f"<i>ID: {notification.id}</i>"

            return message

        except Exception as e:
            self.logger.error(f"Error creating HTML message: {e}")
            return f"{notification.title}\n\n{notification.message}"

    def _create_markdown_message(self, notification: Notification, emoji: str) -> str:
        """Create Markdown formatted message."""
        try:
            message = f"{emoji} *{self._escape_markdown(notification.title)}*\n\n"
            message += f"*Type:* {notification.type.value.upper()}\n"
            message += (
                f"*Time:* {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            message += (
                f"*Priority:* {self._get_priority_text(notification.priority)}\n\n"
            )

            # Add message content
            message += f"*Message:*\n{self._escape_markdown(notification.message)}\n\n"

            # Add metadata if available
            if self.include_metadata and notification.metadata:
                message += f"*Details:*\n"
                for key, value in notification.metadata.items():
                    key_formatted = key.replace("_", " ").title()
                    message += (
                        f"• *{key_formatted}:* {self._escape_markdown(str(value))}\n"
                    )
                message += "\n"

            message += f"_ID: {notification.id}_"

            return message

        except Exception as e:
            self.logger.error(f"Error creating Markdown message: {e}")
            return f"{notification.title}\n\n{notification.message}"

    def _create_plain_message(self, notification: Notification, emoji: str) -> str:
        """Create plain text message."""
        try:
            message = f"{emoji} {notification.title}\n\n"
            message += f"Type: {notification.type.value.upper()}\n"
            message += f"Time: {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            message += f"Priority: {self._get_priority_text(notification.priority)}\n\n"

            # Add message content
            message += f"Message:\n{notification.message}\n\n"

            # Add metadata if available
            if self.include_metadata and notification.metadata:
                message += f"Details:\n"
                for key, value in notification.metadata.items():
                    key_formatted = key.replace("_", " ").title()
                    message += f"• {key_formatted}: {value}\n"
                message += "\n"

            message += f"ID: {notification.id}"

            return message

        except Exception as e:
            self.logger.error(f"Error creating plain message: {e}")
            return f"{notification.title}\n\n{notification.message}"

    def _escape_html(self, text: str) -> str:
        """Escape HTML characters in text."""
        try:
            return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        except Exception:
            return str(text)

    def _escape_markdown(self, text: str) -> str:
        """Escape Markdown characters in text."""
        try:
            return (
                text.replace("_", "\\_")
                .replace("*", "\\*")
                .replace("[", "\\[")
                .replace("]", "\\]")
                .replace("(", "\\(")
                .replace(")", "\\)")
                .replace("~", "\\~")
                .replace("`", "\\`")
                .replace(">", "\\>")
                .replace("#", "\\#")
                .replace("+", "\\+")
                .replace("-", "\\-")
                .replace("=", "\\=")
                .replace("|", "\\|")
                .replace("{", "\\{")
                .replace("}", "\\}")
                .replace(".", "\\.")
                .replace("!", "\\!")
            )
        except Exception:
            return str(text)

    def _get_priority_text(self, priority: int) -> str:
        """Get priority text from priority level."""
        priority_map = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}
        return priority_map.get(priority, "Unknown")

    async def _send_message(self, chat_id: str, message: str) -> bool:
        """
        Send message to specific chat ID.

        Args:
            chat_id: Telegram chat ID
            message: Message to send

        Returns:
            True if sent successfully
        """
        try:
            url = f"{self.api_url}/sendMessage"

            data = {"chat_id": chat_id, "text": message, "parse_mode": self.parse_mode}

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("ok"):
                            return True
                        else:
                            self.logger.error(
                                f"Telegram API error: {result.get('description', 'Unknown error')}"
                            )
                            return False
                    else:
                        self.logger.error(
                            f"HTTP error sending Telegram message: {response.status}"
                        )
                        return False

        except asyncio.TimeoutError:
            self.logger.error("Timeout sending Telegram message")
            return False

        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
            return False

    async def is_available(self) -> bool:
        """
        Check if Telegram notifier is available.

        Returns:
            True if available
        """
        try:
            if aiohttp is None:
                return False

            if not self.bot_token or not self.chat_ids:
                return False

            # Test API connection
            url = f"{self.api_url}/getMe"

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5)
            ) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("ok", False)
                    else:
                        return False

        except Exception as e:
            self.logger.debug(f"Telegram notifier not available: {e}")
            return False

    async def get_bot_info(self) -> Optional[dict]:
        """
        Get bot information.

        Returns:
            Bot information dictionary or None
        """
        try:
            if aiohttp is None:
                return None

            url = f"{self.api_url}/getMe"

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("ok"):
                            return result.get("result")

            return None

        except Exception as e:
            self.logger.error(f"Error getting bot info: {e}")
            return None

    async def close(self):
        """Close Telegram notifier."""
        # No persistent connections to close
        pass

    def __str__(self) -> str:
        """String representation of Telegram notifier."""
        return f"TelegramNotifier(chats={len(self.chat_ids)}, parse_mode={self.parse_mode})"
