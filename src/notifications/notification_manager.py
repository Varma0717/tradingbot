"""
Notification Manager for handling alerts and communications.
Supports multiple notification channels and message types.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Protocol
from dataclasses import dataclass
from enum import Enum

from ..core.config import Config
from ..utils.logger import get_logger


class NotificationType(Enum):
    """Notification type enumeration."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    TRADE = "trade"
    SIGNAL = "signal"
    RISK = "risk"
    SYSTEM = "system"


class NotificationChannel(Enum):
    """Notification channel enumeration."""

    EMAIL = "email"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"


@dataclass
class Notification:
    """Notification object."""

    id: str
    type: NotificationType
    title: str
    message: str
    timestamp: datetime
    channel: Optional[NotificationChannel] = None
    priority: int = 0  # 0=low, 1=medium, 2=high, 3=critical
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "timestamp": self.timestamp,
            "channel": self.channel.value if self.channel else None,
            "priority": self.priority,
            "metadata": self.metadata,
        }


class NotifierProtocol(Protocol):
    """Protocol for notification providers."""

    async def send(self, notification: Notification) -> bool:
        """Send notification."""
        ...

    async def is_available(self) -> bool:
        """Check if notifier is available."""
        ...


class NotificationManager:
    """
    Notification manager for handling alerts and communications.
    """

    def __init__(self, config: Config):
        """
        Initialize notification manager.

        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = get_logger(__name__)

        # Notification settings
        self.enabled = getattr(config.notifications, "enabled", True)
        self.default_channels = getattr(
            config.notifications, "default_channels", ["email"]
        )
        self.rate_limit = getattr(config.notifications, "rate_limit", 60)  # seconds

        # Notification providers
        self.notifiers: Dict[NotificationChannel, NotifierProtocol] = {}

        # Notification queue and tracking
        self.notification_queue: List[Notification] = []
        self.sent_notifications: List[Notification] = []
        self.failed_notifications: List[Notification] = []

        # Rate limiting
        self.last_notification_time: Dict[str, datetime] = {}

        # Initialize notifiers
        self._initialize_notifiers()

    def _initialize_notifiers(self):
        """Initialize notification providers."""
        try:
            # Import and initialize notifiers based on configuration
            notification_config = self.config.notifications

            if (
                hasattr(notification_config, "email")
                and notification_config.email.enabled
            ):
                from .email_notifier import EmailNotifier

                self.notifiers[NotificationChannel.EMAIL] = EmailNotifier(
                    notification_config.email
                )
                self.logger.info("Email notifier initialized")

            if (
                hasattr(notification_config, "telegram")
                and notification_config.telegram.enabled
            ):
                from .telegram_notifier import TelegramNotifier

                self.notifiers[NotificationChannel.TELEGRAM] = TelegramNotifier(
                    notification_config.telegram
                )
                self.logger.info("Telegram notifier initialized")

            if (
                hasattr(notification_config, "webhook")
                and notification_config.webhook.enabled
            ):
                from .webhook_notifier import WebhookNotifier

                self.notifiers[NotificationChannel.WEBHOOK] = WebhookNotifier(
                    notification_config.webhook
                )
                self.logger.info("Webhook notifier initialized")

        except Exception as e:
            self.logger.error(f"Error initializing notifiers: {e}")

    async def send_notification(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        channels: Optional[List[NotificationChannel]] = None,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send a notification.

        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            channels: Channels to send to (optional)
            priority: Priority level (0-3)
            metadata: Additional metadata

        Returns:
            True if sent successfully
        """
        try:
            if not self.enabled:
                return True

            # Create notification object
            notification = Notification(
                id=f"notif_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                type=notification_type,
                title=title,
                message=message,
                timestamp=datetime.now(),
                priority=priority,
                metadata=metadata or {},
            )

            # Determine channels
            if channels is None:
                channels = [NotificationChannel(ch) for ch in self.default_channels]

            # Check rate limiting
            if not self._check_rate_limit(notification):
                self.logger.debug(f"Notification rate limited: {title}")
                return False

            # Send to each channel
            success = True
            for channel in channels:
                try:
                    notification.channel = channel

                    if channel in self.notifiers:
                        result = await self.notifiers[channel].send(notification)
                        if not result:
                            success = False
                            self.failed_notifications.append(notification)
                        else:
                            self.sent_notifications.append(notification)
                    else:
                        self.logger.warning(
                            f"Notifier not available for channel: {channel.value}"
                        )
                        success = False

                except Exception as e:
                    self.logger.error(
                        f"Error sending notification via {channel.value}: {e}"
                    )
                    success = False

            # Update rate limiting
            self._update_rate_limit(notification)

            # Cleanup old notifications
            self._cleanup_notifications()

            return success

        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")
            return False

    async def send_trade_notification(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        status: str,
        strategy: Optional[str] = None,
    ):
        """
        Send trade-specific notification.

        Args:
            symbol: Trading symbol
            side: Trade side
            amount: Trade amount
            price: Trade price
            status: Trade status
            strategy: Strategy name
        """
        try:
            title = f"Trade {status.upper()}: {symbol}"
            message = f"{side.upper()} {amount} {symbol} @ {price}"

            if strategy:
                message += f" (Strategy: {strategy})"

            metadata = {
                "symbol": symbol,
                "side": side,
                "amount": amount,
                "price": price,
                "status": status,
                "strategy": strategy,
            }

            await self.send_notification(
                title=title,
                message=message,
                notification_type=NotificationType.TRADE,
                priority=1,
                metadata=metadata,
            )

        except Exception as e:
            self.logger.error(f"Error sending trade notification: {e}")

    async def send_signal_notification(
        self,
        symbol: str,
        signal_type: str,
        strength: float,
        strategy: str,
        reason: Optional[str] = None,
    ):
        """
        Send trading signal notification.

        Args:
            symbol: Trading symbol
            signal_type: Signal type (BUY/SELL)
            strength: Signal strength
            strategy: Strategy name
            reason: Signal reason
        """
        try:
            title = f"Trading Signal: {signal_type} {symbol}"
            message = f"Strategy: {strategy}\nStrength: {strength:.2f}"

            if reason:
                message += f"\nReason: {reason}"

            metadata = {
                "symbol": symbol,
                "signal_type": signal_type,
                "strength": strength,
                "strategy": strategy,
                "reason": reason,
            }

            await self.send_notification(
                title=title,
                message=message,
                notification_type=NotificationType.SIGNAL,
                priority=1,
                metadata=metadata,
            )

        except Exception as e:
            self.logger.error(f"Error sending signal notification: {e}")

    async def send_risk_alert(
        self, alert_type: str, message: str, severity: str = "medium"
    ):
        """
        Send risk alert notification.

        Args:
            alert_type: Type of risk alert
            message: Alert message
            severity: Alert severity
        """
        try:
            title = f"Risk Alert: {alert_type.replace('_', ' ').title()}"

            # Determine priority based on severity
            priority_map = {"low": 0, "medium": 1, "high": 2, "critical": 3}
            priority = priority_map.get(severity.lower(), 1)

            metadata = {"alert_type": alert_type, "severity": severity}

            await self.send_notification(
                title=title,
                message=message,
                notification_type=NotificationType.RISK,
                priority=priority,
                metadata=metadata,
            )

        except Exception as e:
            self.logger.error(f"Error sending risk alert: {e}")

    async def send_system_notification(
        self, title: str, message: str, level: str = "info"
    ):
        """
        Send system notification.

        Args:
            title: Notification title
            message: Notification message
            level: Log level (info, warning, error, critical)
        """
        try:
            type_map = {
                "info": NotificationType.INFO,
                "warning": NotificationType.WARNING,
                "error": NotificationType.ERROR,
                "critical": NotificationType.CRITICAL,
            }

            notification_type = type_map.get(level.lower(), NotificationType.INFO)
            priority = 1 if level.lower() in ["warning", "error"] else 0
            priority = 3 if level.lower() == "critical" else priority

            await self.send_notification(
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
            )

        except Exception as e:
            self.logger.error(f"Error sending system notification: {e}")

    async def send_portfolio_update(
        self, balance: float, pnl: float, pnl_pct: float, positions: int
    ):
        """
        Send portfolio update notification.

        Args:
            balance: Current balance
            pnl: Total P&L
            pnl_pct: P&L percentage
            positions: Number of active positions
        """
        try:
            title = "Portfolio Update"
            message = f"Balance: ${balance:.2f}\n"
            message += f"P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)\n"
            message += f"Active Positions: {positions}"

            metadata = {
                "balance": balance,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "positions": positions,
            }

            await self.send_notification(
                title=title,
                message=message,
                notification_type=NotificationType.INFO,
                priority=0,
                metadata=metadata,
            )

        except Exception as e:
            self.logger.error(f"Error sending portfolio update: {e}")

    def _check_rate_limit(self, notification: Notification) -> bool:
        """Check if notification passes rate limiting."""
        try:
            # Create rate limit key
            key = f"{notification.type.value}_{notification.title}"

            # Check if we're within rate limit
            if key in self.last_notification_time:
                time_diff = (
                    datetime.now() - self.last_notification_time[key]
                ).total_seconds()
                if time_diff < self.rate_limit:
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking rate limit: {e}")
            return True

    def _update_rate_limit(self, notification: Notification):
        """Update rate limiting tracker."""
        try:
            key = f"{notification.type.value}_{notification.title}"
            self.last_notification_time[key] = datetime.now()

        except Exception as e:
            self.logger.error(f"Error updating rate limit: {e}")

    def _cleanup_notifications(self):
        """Clean up old notifications."""
        try:
            # Keep only last 1000 notifications
            if len(self.sent_notifications) > 1000:
                self.sent_notifications = self.sent_notifications[-1000:]

            if len(self.failed_notifications) > 100:
                self.failed_notifications = self.failed_notifications[-100:]

            # Clean up rate limit tracker (keep only last 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            keys_to_remove = []

            for key, timestamp in self.last_notification_time.items():
                if timestamp < cutoff_time:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.last_notification_time[key]

        except Exception as e:
            self.logger.error(f"Error cleaning up notifications: {e}")

    async def test_notifications(self) -> Dict[str, bool]:
        """
        Test all notification channels.

        Returns:
            Dictionary with test results for each channel
        """
        results = {}

        for channel, notifier in self.notifiers.items():
            try:
                # Check availability
                available = await notifier.is_available()

                if available:
                    # Send test notification
                    test_notification = Notification(
                        id="test_notification",
                        type=NotificationType.SYSTEM,
                        title="Test Notification",
                        message="This is a test notification from the trading bot.",
                        timestamp=datetime.now(),
                        channel=channel,
                    )

                    success = await notifier.send(test_notification)
                    results[channel.value] = success
                else:
                    results[channel.value] = False
                    self.logger.warning(f"Notifier not available: {channel.value}")

            except Exception as e:
                self.logger.error(f"Error testing {channel.value} notifier: {e}")
                results[channel.value] = False

        return results

    def get_notification_stats(self) -> Dict[str, Any]:
        """
        Get notification statistics.

        Returns:
            Dictionary with notification statistics
        """
        try:
            total_sent = len(self.sent_notifications)
            total_failed = len(self.failed_notifications)

            # Count by type
            type_counts = {}
            for notification in self.sent_notifications:
                notification_type = notification.type.value
                type_counts[notification_type] = (
                    type_counts.get(notification_type, 0) + 1
                )

            # Count by channel
            channel_counts = {}
            for notification in self.sent_notifications:
                if notification.channel:
                    channel = notification.channel.value
                    channel_counts[channel] = channel_counts.get(channel, 0) + 1

            return {
                "total_sent": total_sent,
                "total_failed": total_failed,
                "success_rate": (
                    (total_sent / (total_sent + total_failed) * 100)
                    if (total_sent + total_failed) > 0
                    else 0.0
                ),
                "enabled": self.enabled,
                "available_channels": list(self.notifiers.keys()),
                "type_counts": type_counts,
                "channel_counts": channel_counts,
                "last_updated": datetime.now(),
            }

        except Exception as e:
            self.logger.error(f"Error getting notification stats: {e}")
            return {}

    def enable_notifications(self):
        """Enable notifications."""
        self.enabled = True
        self.logger.info("Notifications enabled")

    def disable_notifications(self):
        """Disable notifications."""
        self.enabled = False
        self.logger.info("Notifications disabled")

    async def close(self):
        """Close notification manager."""
        try:
            # Close all notifiers
            for notifier in self.notifiers.values():
                if hasattr(notifier, "close"):
                    await notifier.close()

            self.logger.info("Notification manager closed")

        except Exception as e:
            self.logger.error(f"Error closing notification manager: {e}")

    def __str__(self) -> str:
        """String representation of notification manager."""
        enabled_channels = list(self.notifiers.keys())
        return (
            f"NotificationManager(enabled={self.enabled}, channels={enabled_channels})"
        )
