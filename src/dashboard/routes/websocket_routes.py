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
    """Get comprehensive dashboard data for WebSocket."""
    try:
        if not _trading_bot:
            return {
                "status": "disconnected",
                "portfolio": {},
                "orders": {},
                "strategies": {},
            }

        # Get all dashboard data
        portfolio_data = await get_portfolio_data()
        orders_data = await get_orders_data()
        strategies_data = await get_strategies_data()

        return {
            "status": "running",
            "portfolio": portfolio_data,
            "orders": orders_data,
            "strategies": strategies_data,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return {"status": "error", "error": str(e)}


async def get_portfolio_data() -> dict:
    """Get portfolio data for WebSocket."""
    try:
        if not _trading_bot or not hasattr(_trading_bot, "portfolio_manager"):
            return {}

        performance = _trading_bot.portfolio_manager.get_portfolio_performance()
        positions = _trading_bot.portfolio_manager.get_positions()

        return {
            "performance": performance,
            "positions": {
                symbol: {
                    "symbol": symbol,
                    "side": position.side.value,
                    "size": position.size,
                    "unrealized_pnl": position.unrealized_pnl,
                    "pnl_percentage": position.pnl_percentage(),
                }
                for symbol, position in positions.items()
            },
        }

    except Exception as e:
        logger.error(f"Error getting portfolio data: {e}")
        return {}


async def get_orders_data() -> dict:
    """Get orders data for WebSocket."""
    try:
        if not _trading_bot or not hasattr(_trading_bot, "order_manager"):
            return {}

        active_orders = _trading_bot.order_manager.get_active_orders()
        order_stats = _trading_bot.order_manager.get_order_stats()

        return {
            "active_orders": {
                order_id: {
                    "id": order.id,
                    "symbol": order.symbol,
                    "side": order.side,
                    "amount": order.amount,
                    "status": order.status.value,
                    "created_at": order.created_at.isoformat(),
                }
                for order_id, order in active_orders.items()
            },
            "stats": order_stats,
        }

    except Exception as e:
        logger.error(f"Error getting orders data: {e}")
        return {}


async def get_trades_data() -> dict:
    """Get trades data for WebSocket."""
    try:
        if not _trading_bot or not hasattr(_trading_bot, "portfolio_manager"):
            return {}

        # Get recent trades (last 10)
        recent_trades = _trading_bot.portfolio_manager.trades[-10:]

        return {
            "recent_trades": [
                {
                    "id": trade.id,
                    "symbol": trade.symbol,
                    "side": trade.side,
                    "amount": trade.amount,
                    "price": trade.price,
                    "timestamp": trade.timestamp.isoformat(),
                }
                for trade in recent_trades
            ]
        }

    except Exception as e:
        logger.error(f"Error getting trades data: {e}")
        return {}


async def get_strategies_data() -> dict:
    """Get strategies data for WebSocket."""
    try:
        if not _trading_bot or not hasattr(_trading_bot, "strategies"):
            return {}

        return {
            "strategies": {
                name: {
                    "name": name,
                    "enabled": strategy.enabled,
                    "signals_count": len(getattr(strategy, "signals", [])),
                    "last_signal": getattr(strategy, "last_signal_time", None),
                }
                for name, strategy in _trading_bot.strategies.items()
            }
        }

    except Exception as e:
        logger.error(f"Error getting strategies data: {e}")
        return {}
