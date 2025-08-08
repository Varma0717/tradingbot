"""
WebSocket routes for real-time updates.
"""

import asyncio
import json
from datetime import datetime
from typing import Optional

try:
    from fastapi import APIRouter, WebSocket, WebSocketDisconnect
    from fastapi.websockets import WebSocketState
except ImportError:
    APIRouter = None
    WebSocket = None

from ...core.bot import TradingBot
from ...utils.logger import get_logger

# Create router
router = APIRouter() if APIRouter else None
logger = get_logger(__name__)

# Connected WebSocket clients
connected_clients = set()
_trading_bot: Optional[TradingBot] = None


def set_trading_bot(trading_bot: TradingBot):
    """Set the trading bot instance for WebSocket access."""
    global _trading_bot
    _trading_bot = trading_bot


@router.websocket("/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    connected_clients.add(websocket)
    logger.info(f"WebSocket client connected. Total clients: {len(connected_clients)}")

    try:
        # Send initial data
        await send_initial_data(websocket)

        # Start periodic updates for this client
        update_task = asyncio.create_task(periodic_updates(websocket))

        # Handle incoming messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                await handle_client_message(websocket, message)

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": "Invalid JSON format"})
                )
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await websocket.send_text(
                    json.dumps({"type": "error", "message": str(e)})
                )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cleanup
        connected_clients.discard(websocket)
        if "update_task" in locals():
            update_task.cancel()
        logger.info(
            f"WebSocket client disconnected. Total clients: {len(connected_clients)}"
        )


async def send_initial_data(websocket: WebSocket):
    """Send initial data to newly connected client."""
    try:
        initial_data = await get_dashboard_data()

        await websocket.send_text(
            json.dumps(
                {
                    "type": "initial_data",
                    "data": initial_data,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        )

    except Exception as e:
        logger.error(f"Error sending initial data: {e}")


async def handle_client_message(websocket: WebSocket, message: dict):
    """Handle incoming messages from WebSocket client."""
    try:
        message_type = message.get("type")

        if message_type == "ping":
            # Respond to ping with pong
            await websocket.send_text(
                json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()})
            )

        elif message_type == "subscribe":
            # Handle subscription to specific data streams
            stream = message.get("stream")
            await handle_subscription(websocket, stream)

        elif message_type == "unsubscribe":
            # Handle unsubscription from data streams
            stream = message.get("stream")
            await handle_unsubscription(websocket, stream)

        elif message_type == "request_data":
            # Handle one-time data requests
            data_type = message.get("data_type")
            await handle_data_request(websocket, data_type)

        else:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "error",
                        "message": f"Unknown message type: {message_type}",
                    }
                )
            )

    except Exception as e:
        logger.error(f"Error handling client message: {e}")


async def handle_subscription(websocket: WebSocket, stream: str):
    """Handle subscription to a data stream."""
    try:
        # Store subscription preferences (in a real app, you'd store this per client)
        await websocket.send_text(
            json.dumps(
                {
                    "type": "subscription_confirmed",
                    "stream": stream,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        )

    except Exception as e:
        logger.error(f"Error handling subscription: {e}")


async def handle_unsubscription(websocket: WebSocket, stream: str):
    """Handle unsubscription from a data stream."""
    try:
        await websocket.send_text(
            json.dumps(
                {
                    "type": "unsubscription_confirmed",
                    "stream": stream,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        )

    except Exception as e:
        logger.error(f"Error handling unsubscription: {e}")


async def handle_data_request(websocket: WebSocket, data_type: str):
    """Handle one-time data requests."""
    try:
        if data_type == "portfolio":
            data = await get_portfolio_data()
        elif data_type == "orders":
            data = await get_orders_data()
        elif data_type == "trades":
            data = await get_trades_data()
        elif data_type == "strategies":
            data = await get_strategies_data()
        else:
            data = {"error": f"Unknown data type: {data_type}"}

        await websocket.send_text(
            json.dumps(
                {
                    "type": "data_response",
                    "data_type": data_type,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        )

    except Exception as e:
        logger.error(f"Error handling data request: {e}")


async def periodic_updates(websocket: WebSocket):
    """Send periodic updates to a specific client."""
    try:
        while websocket.client_state == WebSocketState.CONNECTED:
            # Get current dashboard data
            dashboard_data = await get_dashboard_data()

            # Send update
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "periodic_update",
                        "data": dashboard_data,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            )

            # Wait 5 seconds before next update
            await asyncio.sleep(5)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Error in periodic updates: {e}")


async def broadcast_update(update_data: dict):
    """Broadcast update to all connected clients."""
    if not connected_clients:
        return

    message = json.dumps(
        {
            "type": "broadcast_update",
            "data": update_data,
            "timestamp": datetime.now().isoformat(),
        }
    )

    disconnected_clients = set()

    for client in connected_clients:
        try:
            if client.client_state == WebSocketState.CONNECTED:
                await client.send_text(message)
            else:
                disconnected_clients.add(client)
        except Exception as e:
            logger.error(f"Error broadcasting to client: {e}")
            disconnected_clients.add(client)

    # Remove disconnected clients
    for client in disconnected_clients:
        connected_clients.discard(client)


async def get_dashboard_data() -> dict:
    """Get comprehensive dashboard data for WebSocket using trading mode manager."""
    try:
        from ...core.trading_mode_manager import trading_mode_manager

        # Get current trading mode status
        mode_status = trading_mode_manager.get_status()

        # Get active strategy manager
        manager = trading_mode_manager.get_active_strategy_manager()

        if not manager:
            return {
                "status": "disconnected",
                "portfolio": {},
                "orders": {},
                "strategies": {},
                "mode": mode_status,
            }

        # Get all dashboard data from active manager
        portfolio_data = await get_portfolio_data()
        orders_data = await get_orders_data()
        strategies_data = await get_strategies_data()

        return {
            "status": "running",
            "portfolio": portfolio_data,
            "orders": orders_data,
            "strategies": strategies_data,
            "mode": mode_status,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return {"status": "error", "error": str(e)}


async def get_portfolio_data() -> dict:
    """Get portfolio data for WebSocket using trading mode manager."""
    try:
        from ...core.trading_mode_manager import trading_mode_manager

        mode_status = trading_mode_manager.get_status()
        balance = trading_mode_manager.get_balance()

        manager = trading_mode_manager.get_active_strategy_manager()

        if not manager:
            return {
                "balance": balance,
                "mode": mode_status.get("mode", "paper"),
                "performance": {},
                "positions": {},
            }

        # Get trades for performance calculation
        trades = manager.get_trades() if hasattr(manager, "get_trades") else []
        total_profit = sum(
            trade.get("profit", 0) for trade in trades if isinstance(trade, dict)
        )

        return {
            "balance": balance,
            "mode": mode_status.get("mode", "paper"),
            "performance": {
                "total_value": balance,
                "total_profit": total_profit,
                "profit_percentage": (
                    (total_profit / balance * 100) if balance > 0 else 0
                ),
            },
            "positions": {},  # Could be extended to show actual positions
        }

    except Exception as e:
        logger.error(f"Error getting portfolio data: {e}")
        return {}


async def get_orders_data() -> dict:
    """Get orders data for WebSocket using trading mode manager."""
    try:
        from ...core.trading_mode_manager import trading_mode_manager

        manager = trading_mode_manager.get_active_strategy_manager()

        if not manager or not hasattr(manager, "get_active_orders"):
            return {"active_orders": {}, "stats": {"total": 0}}

        orders = manager.get_active_orders()

        return {
            "active_orders": {
                str(i): {
                    "id": order.get("id", f"order_{i}"),
                    "symbol": order.get("strategy", "BTCUSDT"),
                    "side": order.get("type", "buy"),
                    "amount": order.get("amount", 0),
                    "price": order.get("price", 0),
                    "status": "open",
                    "created_at": order.get("created", datetime.now().isoformat()),
                }
                for i, order in enumerate(orders)
                if isinstance(order, dict)
            },
            "stats": {"total": len(orders)},
        }

    except Exception as e:
        logger.error(f"Error getting orders data: {e}")
        return {}


async def get_trades_data() -> dict:
    """Get trades data for WebSocket using trading mode manager."""
    try:
        from ...core.trading_mode_manager import trading_mode_manager

        manager = trading_mode_manager.get_active_strategy_manager()

        if not manager or not hasattr(manager, "get_trades"):
            return {"recent_trades": []}

        trades = manager.get_trades()

        # Get recent trades (last 10)
        recent_trades = trades[-10:] if trades else []

        return {
            "recent_trades": [
                {
                    "id": trade.get("id", f"trade_{i}"),
                    "symbol": trade.get("symbol", "BTCUSDT"),
                    "side": trade.get("side", "buy"),
                    "amount": trade.get("amount", 0),
                    "price": trade.get("price", 0),
                    "profit": trade.get("profit", 0),
                    "timestamp": trade.get("timestamp", datetime.now().isoformat()),
                }
                for i, trade in enumerate(recent_trades)
                if isinstance(trade, dict)
            ]
        }

    except Exception as e:
        logger.error(f"Error getting trades data: {e}")
        return {}


async def get_strategies_data() -> dict:
    """Get strategies data for WebSocket using trading mode manager."""
    try:
        from ...core.trading_mode_manager import trading_mode_manager

        manager = trading_mode_manager.get_active_strategy_manager()
        mode_status = trading_mode_manager.get_status()

        if not manager:
            return {
                "strategies": {
                    "inactive": {
                        "name": "No Active Strategy",
                        "enabled": False,
                        "signals_count": 0,
                        "last_signal": None,
                    }
                }
            }

        status = manager.get_status() if hasattr(manager, "get_status") else {}

        return {
            "strategies": {
                "grid_dca": {
                    "name": f"Grid DCA ({mode_status.get('mode', 'paper')} mode)",
                    "enabled": status.get("is_running", False),
                    "signals_count": 0,  # Could be extended
                    "last_signal": (
                        datetime.now().isoformat() if status.get("is_running") else None
                    ),
                }
            }
        }

    except Exception as e:
        logger.error(f"Error getting strategies data: {e}")
        return {}
