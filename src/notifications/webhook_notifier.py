"""
Webhook Notifier for sending notifications via HTTP webhooks.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any

try:
    import aiohttp
except ImportError:
    aiohttp = None

from ..utils.logger import get_logger
from .notification_manager import Notification, NotificationType


class WebhookNotifier:
    """
    Webhook notifier for sending notifications via HTTP webhooks.
    """

    def __init__(self, config):
        """
        Initialize webhook notifier.

        Args:
            config: Webhook configuration object
        """
        self.config = config
        self.logger = get_logger(__name__)

        # Webhook settings
        self.webhooks = getattr(config, "webhooks", [])
        self.timeout = getattr(config, "timeout", 30)
        self.retries = getattr(config, "retries", 3)
        self.retry_delay = getattr(config, "retry_delay", 1)

        # Authentication
        self.auth_headers = getattr(config, "auth_headers", {})
        self.auth_type = getattr(
            config, "auth_type", None
        )  # 'bearer', 'basic', 'api_key'
        self.auth_token = getattr(config, "auth_token", "")

        # Message formatting
        self.format_type = getattr(
            config, "format_type", "json"
        )  # 'json', 'form', 'slack', 'discord'
        self.include_metadata = getattr(config, "include_metadata", True)

        # Check if aiohttp is available
        if aiohttp is None:
            self.logger.warning(
                "aiohttp not available - Webhook notifications will not work"
            )

    async def send(self, notification: Notification) -> bool:
        """
        Send notification via webhooks.

        Args:
            notification: Notification to send

        Returns:
            True if sent successfully to at least one webhook
        """
        try:
            if aiohttp is None:
                self.logger.error("aiohttp not available for webhook notifications")
                return False

            if not self.webhooks:
                self.logger.warning("No webhooks configured")
                return False

            # Create payload
            payload = self._create_payload(notification)

            # Send to all webhooks
            success_count = 0
            for webhook in self.webhooks:
                result = await self._send_webhook(webhook, payload, notification)
                if result:
                    success_count += 1

            success = success_count > 0

            if success:
                self.logger.info(
                    f"Webhook notification sent to {success_count}/{len(self.webhooks)} endpoints: {notification.title}"
                )
            else:
                self.logger.error(
                    f"Failed to send webhook notification to any endpoint: {notification.title}"
                )

            return success

        except Exception as e:
            self.logger.error(f"Error sending webhook notification: {e}")
            return False

    def _create_payload(self, notification: Notification) -> Dict[str, Any]:
        """
        Create webhook payload from notification.

        Args:
            notification: Notification object

        Returns:
            Payload dictionary
        """
        try:
            if self.format_type == "slack":
                return self._create_slack_payload(notification)
            elif self.format_type == "discord":
                return self._create_discord_payload(notification)
            elif self.format_type == "teams":
                return self._create_teams_payload(notification)
            else:
                return self._create_json_payload(notification)

        except Exception as e:
            self.logger.error(f"Error creating webhook payload: {e}")
            return self._create_json_payload(notification)

    def _create_json_payload(self, notification: Notification) -> Dict[str, Any]:
        """Create standard JSON payload."""
        try:
            payload = {
                "id": notification.id,
                "type": notification.type.value,
                "title": notification.title,
                "message": notification.message,
                "timestamp": notification.timestamp.isoformat(),
                "priority": notification.priority,
                "priority_text": self._get_priority_text(notification.priority),
            }

            if self.include_metadata and notification.metadata:
                payload["metadata"] = notification.metadata

            # Add trading bot identification
            payload["source"] = "crypto_trading_bot"
            payload["version"] = "1.0.0"

            return payload

        except Exception as e:
            self.logger.error(f"Error creating JSON payload: {e}")
            return {
                "title": notification.title,
                "message": notification.message,
                "timestamp": notification.timestamp.isoformat(),
            }

    def _create_slack_payload(self, notification: Notification) -> Dict[str, Any]:
        """Create Slack-compatible payload."""
        try:
            # Color mapping for notification types
            color_map = {
                "info": "#36a64f",  # Good (green)
                "warning": "#ffcc00",  # Warning (yellow)
                "error": "#ff0000",  # Danger (red)
                "critical": "#800080",  # Purple
                "trade": "#00ff00",  # Bright green
                "signal": "#0099ff",  # Blue
                "risk": "#ff6600",  # Orange
                "system": "#888888",  # Gray
            }

            color = color_map.get(notification.type.value, "#888888")

            # Create attachment
            attachment = {
                "color": color,
                "title": notification.title,
                "text": notification.message,
                "timestamp": int(notification.timestamp.timestamp()),
                "fields": [
                    {
                        "title": "Type",
                        "value": notification.type.value.upper(),
                        "short": True,
                    },
                    {
                        "title": "Priority",
                        "value": self._get_priority_text(notification.priority),
                        "short": True,
                    },
                ],
            }

            # Add metadata as fields
            if self.include_metadata and notification.metadata:
                for key, value in notification.metadata.items():
                    attachment["fields"].append(
                        {
                            "title": key.replace("_", " ").title(),
                            "value": str(value),
                            "short": True,
                        }
                    )

            payload = {"text": f"🤖 Trading Bot Alert", "attachments": [attachment]}

            return payload

        except Exception as e:
            self.logger.error(f"Error creating Slack payload: {e}")
            return {"text": f"{notification.title}: {notification.message}"}

    def _create_discord_payload(self, notification: Notification) -> Dict[str, Any]:
        """Create Discord-compatible payload."""
        try:
            # Color mapping for notification types (Discord uses decimal colors)
            color_map = {
                "info": 3447003,  # Blue
                "warning": 16776960,  # Yellow
                "error": 16711680,  # Red
                "critical": 8388736,  # Purple
                "trade": 65280,  # Green
                "signal": 39423,  # Light blue
                "risk": 16753920,  # Orange
                "system": 8947848,  # Gray
            }

            color = color_map.get(notification.type.value, 8947848)

            # Create embed
            embed = {
                "title": notification.title,
                "description": notification.message,
                "color": color,
                "timestamp": notification.timestamp.isoformat(),
                "footer": {
                    "text": f"Trading Bot • {notification.type.value.upper()} • Priority: {self._get_priority_text(notification.priority)}"
                },
                "fields": [],
            }

            # Add metadata as fields
            if self.include_metadata and notification.metadata:
                for key, value in notification.metadata.items():
                    embed["fields"].append(
                        {
                            "name": key.replace("_", " ").title(),
                            "value": str(value),
                            "inline": True,
                        }
                    )

            payload = {"content": "🤖 **Trading Bot Notification**", "embeds": [embed]}

            return payload

        except Exception as e:
            self.logger.error(f"Error creating Discord payload: {e}")
            return {"content": f"**{notification.title}**\n{notification.message}"}

    def _create_teams_payload(self, notification: Notification) -> Dict[str, Any]:
        """Create Microsoft Teams-compatible payload."""
        try:
            # Color mapping for notification types
            color_map = {
                "info": "0078D4",
                "warning": "FFB900",
                "error": "D13438",
                "critical": "8764B8",
                "trade": "107C10",
                "signal": "00BCF2",
                "risk": "FF8C00",
                "system": "737373",
            }

            color = color_map.get(notification.type.value, "737373")

            # Create facts (metadata)
            facts = [
                {"name": "Type", "value": notification.type.value.upper()},
                {
                    "name": "Priority",
                    "value": self._get_priority_text(notification.priority),
                },
                {
                    "name": "Time",
                    "value": notification.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                },
            ]

            if self.include_metadata and notification.metadata:
                for key, value in notification.metadata.items():
                    facts.append(
                        {"name": key.replace("_", " ").title(), "value": str(value)}
                    )

            payload = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": notification.title,
                "themeColor": color,
                "sections": [
                    {
                        "activityTitle": "🤖 Trading Bot Notification",
                        "activitySubtitle": notification.title,
                        "text": notification.message,
                        "facts": facts,
                    }
                ],
            }

            return payload

        except Exception as e:
            self.logger.error(f"Error creating Teams payload: {e}")
            return {
                "@type": "MessageCard",
                "summary": notification.title,
                "text": f"**{notification.title}**\n\n{notification.message}",
            }

    def _get_priority_text(self, priority: int) -> str:
        """Get priority text from priority level."""
        priority_map = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}
        return priority_map.get(priority, "Unknown")

    async def _send_webhook(
        self,
        webhook_config: Dict[str, Any],
        payload: Dict[str, Any],
        notification: Notification,
    ) -> bool:
        """
        Send webhook to specific endpoint.

        Args:
            webhook_config: Webhook configuration
            payload: Payload to send
            notification: Original notification

        Returns:
            True if sent successfully
        """
        try:
            url = webhook_config.get("url")
            if not url:
                self.logger.error("Webhook URL not configured")
                return False

            # Prepare headers
            headers = {"Content-Type": "application/json"}
            headers.update(self.auth_headers)

            # Add authentication
            if self.auth_type == "bearer" and self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            elif self.auth_type == "api_key" and self.auth_token:
                headers["X-API-Key"] = self.auth_token

            # Override headers from webhook config
            if "headers" in webhook_config:
                headers.update(webhook_config["headers"])

            # Retry logic
            for attempt in range(self.retries + 1):
                try:
                    async with aiohttp.ClientSession(
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as session:
                        async with session.post(
                            url, json=payload, headers=headers
                        ) as response:
                            if response.status in [200, 201, 202, 204]:
                                self.logger.debug(f"Webhook sent successfully to {url}")
                                return True
                            else:
                                self.logger.warning(
                                    f"Webhook returned status {response.status} for {url}"
                                )

                                # Log response body for debugging
                                try:
                                    response_text = await response.text()
                                    self.logger.debug(
                                        f"Webhook response: {response_text[:500]}"
                                    )
                                except Exception:
                                    pass

                                if attempt < self.retries:
                                    await asyncio.sleep(self.retry_delay)
                                    continue
                                else:
                                    return False

                except asyncio.TimeoutError:
                    self.logger.warning(
                        f"Webhook timeout for {url} (attempt {attempt + 1})"
                    )
                    if attempt < self.retries:
                        await asyncio.sleep(self.retry_delay)
                        continue
                    else:
                        return False

                except Exception as e:
                    self.logger.error(
                        f"Error sending webhook to {url} (attempt {attempt + 1}): {e}"
                    )
                    if attempt < self.retries:
                        await asyncio.sleep(self.retry_delay)
                        continue
                    else:
                        return False

            return False

        except Exception as e:
            self.logger.error(f"Error in webhook send: {e}")
            return False

    async def is_available(self) -> bool:
        """
        Check if webhook notifier is available.

        Returns:
            True if available
        """
        try:
            if aiohttp is None:
                return False

            if not self.webhooks:
                return False

            # Test first webhook
            webhook = self.webhooks[0]
            url = webhook.get("url")

            if not url:
                return False

            # Simple connectivity test
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5)
            ) as session:
                async with session.head(url) as response:
                    # Accept any response (including 404, 405) as long as we can connect
                    return True

        except Exception as e:
            self.logger.debug(f"Webhook notifier not available: {e}")
            return False

    async def test_webhook(self, webhook_url: str) -> bool:
        """
        Test a specific webhook URL.

        Args:
            webhook_url: Webhook URL to test

        Returns:
            True if test successful
        """
        try:
            if aiohttp is None:
                return False

            # Create test payload
            test_notification = Notification(
                id="test_webhook",
                type=NotificationType.SYSTEM,
                title="Webhook Test",
                message="This is a test notification to verify webhook connectivity.",
                timestamp=datetime.now(),
            )

            payload = self._create_payload(test_notification)

            # Send test webhook
            webhook_config = {"url": webhook_url}
            return await self._send_webhook(webhook_config, payload, test_notification)

        except Exception as e:
            self.logger.error(f"Error testing webhook {webhook_url}: {e}")
            return False

    async def close(self):
        """Close webhook notifier."""
        # No persistent connections to close
        pass

    def __str__(self) -> str:
        """String representation of webhook notifier."""
        return f"WebhookNotifier(endpoints={len(self.webhooks)}, format={self.format_type})"
