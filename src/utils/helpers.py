"""
Utility helper functions for the trading bot.
"""

import hashlib
import hmac
import base64
import time
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal, ROUND_HALF_UP


def round_to_precision(value: float, precision: int) -> float:
    """
    Round a value to the specified precision.

    Args:
        value: Value to round
        precision: Number of decimal places

    Returns:
        Rounded value
    """
    decimal_value = Decimal(str(value))
    return float(
        decimal_value.quantize(Decimal("0." + "0" * precision), rounding=ROUND_HALF_UP)
    )


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    Calculate percentage change between two values.

    Args:
        old_value: Original value
        new_value: New value

    Returns:
        Percentage change
    """
    if old_value == 0:
        return 0.0
    return ((new_value - old_value) / old_value) * 100


def format_currency(amount: float, currency: str = "USD", decimals: int = 2) -> str:
    """
    Format a currency amount for display.

    Args:
        amount: Amount to format
        currency: Currency symbol
        decimals: Number of decimal places

    Returns:
        Formatted currency string
    """
    return f"{amount:,.{decimals}f} {currency}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format a percentage value for display.

    Args:
        value: Percentage value
        decimals: Number of decimal places

    Returns:
        Formatted percentage string
    """
    return f"{value:.{decimals}f}%"


def timestamp_to_datetime(timestamp: Union[int, float]) -> datetime:
    """
    Convert timestamp to datetime object.

    Args:
        timestamp: Unix timestamp

    Returns:
        Datetime object
    """
    # Handle both seconds and milliseconds timestamps
    if timestamp > 1e10:  # Milliseconds
        timestamp = timestamp / 1000

    return datetime.fromtimestamp(timestamp)


def datetime_to_timestamp(dt: datetime) -> int:
    """
    Convert datetime to unix timestamp.

    Args:
        dt: Datetime object

    Returns:
        Unix timestamp in milliseconds
    """
    return int(dt.timestamp() * 1000)


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert a value to float.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Float value or default
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert a value to integer.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Integer value or default
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def generate_signature(secret: str, message: str, algorithm: str = "sha256") -> str:
    """
    Generate HMAC signature for API authentication.

    Args:
        secret: Secret key
        message: Message to sign
        algorithm: Hash algorithm

    Returns:
        HMAC signature
    """
    secret_bytes = secret.encode("utf-8")
    message_bytes = message.encode("utf-8")

    if algorithm == "sha256":
        signature = hmac.new(secret_bytes, message_bytes, hashlib.sha256)
    elif algorithm == "sha512":
        signature = hmac.new(secret_bytes, message_bytes, hashlib.sha512)
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    return signature.hexdigest()


def generate_base64_signature(secret: str, message: str) -> str:
    """
    Generate base64-encoded HMAC signature.

    Args:
        secret: Secret key
        message: Message to sign

    Returns:
        Base64-encoded signature
    """
    secret_bytes = base64.b64decode(secret)
    message_bytes = message.encode("utf-8")
    signature = hmac.new(secret_bytes, message_bytes, hashlib.sha256)
    return base64.b64encode(signature.digest()).decode("utf-8")


def validate_symbol(symbol: str) -> bool:
    """
    Validate trading symbol format.

    Args:
        symbol: Trading symbol (e.g., 'BTC/USDT')

    Returns:
        True if valid, False otherwise
    """
    if not symbol or "/" not in symbol:
        return False

    parts = symbol.split("/")
    if len(parts) != 2:
        return False

    base, quote = parts
    return bool(base and quote and base.isalpha() and quote.isalpha())


def calculate_position_size(
    balance: float, risk_percentage: float, entry_price: float, stop_loss_price: float
) -> float:
    """
    Calculate position size based on risk management.

    Args:
        balance: Account balance
        risk_percentage: Risk percentage (0.02 for 2%)
        entry_price: Entry price
        stop_loss_price: Stop loss price

    Returns:
        Position size
    """
    if entry_price <= 0 or stop_loss_price <= 0:
        return 0.0

    risk_amount = balance * risk_percentage
    price_difference = abs(entry_price - stop_loss_price)

    if price_difference == 0:
        return 0.0

    position_size = risk_amount / price_difference
    return position_size


def calculate_kelly_criterion(
    win_rate: float, avg_win: float, avg_loss: float
) -> float:
    """
    Calculate Kelly Criterion for optimal position sizing.

    Args:
        win_rate: Probability of winning (0.0 to 1.0)
        avg_win: Average winning amount
        avg_loss: Average losing amount

    Returns:
        Kelly percentage (0.0 to 1.0)
    """
    if avg_loss <= 0 or win_rate <= 0 or win_rate >= 1:
        return 0.0

    odds = avg_win / avg_loss
    kelly = (win_rate * odds - (1 - win_rate)) / odds

    # Cap at 25% for safety
    return max(0.0, min(0.25, kelly))


def split_symbol(symbol: str) -> tuple:
    """
    Split trading symbol into base and quote currencies.

    Args:
        symbol: Trading symbol (e.g., 'BTC/USDT')

    Returns:
        Tuple of (base, quote) currencies
    """
    if "/" in symbol:
        return tuple(symbol.split("/"))
    return ("", "")


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple dictionaries.

    Args:
        *dicts: Dictionaries to merge

    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.

    Args:
        lst: List to split
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def retry_on_exception(
    func,
    exceptions: tuple = (Exception,),
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
):
    """
    Decorator to retry function on exception.

    Args:
        func: Function to retry
        exceptions: Tuple of exceptions to catch
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        backoff: Backoff multiplier

    Returns:
        Decorated function
    """

    def wrapper(*args, **kwargs):
        current_delay = delay
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if attempt == max_retries:
                    raise e
                time.sleep(current_delay)
                current_delay *= backoff

    return wrapper


def calculate_drawdown(equity_curve: List[float]) -> Dict[str, float]:
    """
    Calculate maximum drawdown from equity curve.

    Args:
        equity_curve: List of equity values

    Returns:
        Dictionary with drawdown metrics
    """
    if not equity_curve:
        return {"max_drawdown": 0.0, "current_drawdown": 0.0}

    peak = equity_curve[0]
    max_drawdown = 0.0
    current_drawdown = 0.0

    for value in equity_curve:
        if value > peak:
            peak = value
            current_drawdown = 0.0
        else:
            current_drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, current_drawdown)

    return {
        "max_drawdown": max_drawdown,
        "current_drawdown": current_drawdown,
        "peak_value": peak,
    }


def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sharpe ratio from returns.

    Args:
        returns: List of returns
        risk_free_rate: Risk-free rate (annual)

    Returns:
        Sharpe ratio
    """
    if not returns or len(returns) < 2:
        return 0.0

    avg_return = sum(returns) / len(returns)
    variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
    std_dev = variance**0.5

    if std_dev == 0:
        return 0.0

    # Adjust risk-free rate for period
    adjusted_risk_free = risk_free_rate / 252  # Daily rate

    return (avg_return - adjusted_risk_free) / std_dev


def format_time_duration(seconds: float) -> str:
    """
    Format time duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:
        days = seconds / 86400
        return f"{days:.1f}d"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for filesystem compatibility.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    return filename


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.

    Args:
        dict1: First dictionary
        dict2: Second dictionary

    Returns:
        Merged dictionary
    """
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result
