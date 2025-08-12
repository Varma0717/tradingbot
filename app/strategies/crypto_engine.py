import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import current_app
from ..exchange_adapter.binance_adapter import BinanceAdapter
from ..models import Order, Trade, Strategy, User, db


class CryptoStrategyEngine:
    def __init__(self, user_id=None, force_paper_mode=True):
        self.user_id = user_id
        # For now, always use paper mode to avoid API authentication issues
        self.binance = BinanceAdapter(
            user_id=user_id, force_paper_mode=force_paper_mode
        )
        self.is_running = False
        self.active_strategies = {}

    def start_trading(self, user_id, strategy_names=None, is_paper=True):
        """Start crypto trading with specified strategies"""
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError("User not found")

            # Default crypto strategies if none specified
            if not strategy_names:
                strategy_names = [
                    "crypto_momentum",
                    "crypto_mean_reversion",
                    "crypto_breakout",
                ]

            current_app.logger.info(
                f"Starting crypto trading for user {user_id} with strategies: {strategy_names}"
            )

            # Check Binance connection for live trading
            if not is_paper and not self.binance.is_connected:
                try:
                    self.binance.connect()
                except Exception as e:
                    current_app.logger.error(f"Failed to connect to Binance: {str(e)}")
                    raise ConnectionError(
                        "Unable to connect to Binance. Please check your API credentials."
                    )

            self.is_running = True

            # Initialize active strategies tracking
            self.active_strategies = {
                name: {
                    "start_time": datetime.now().strftime("%H:%M UTC"),
                    "trades_count": 0,
                }
                for name in strategy_names
            }

            # Update database status
            self._update_bot_status(is_running=True, strategies=strategy_names)

            # Get top crypto pairs for trading
            crypto_symbols = self.get_crypto_watchlist()

            results = {}
            for strategy_name in strategy_names:
                try:
                    if strategy_name == "crypto_momentum":
                        result = self.run_momentum_strategy(
                            user_id, crypto_symbols, is_paper
                        )
                    elif strategy_name == "crypto_mean_reversion":
                        result = self.run_mean_reversion_strategy(
                            user_id, crypto_symbols, is_paper
                        )
                    elif strategy_name == "crypto_breakout":
                        result = self.run_breakout_strategy(
                            user_id, crypto_symbols, is_paper
                        )
                    else:
                        current_app.logger.warning(
                            f"Unknown crypto strategy: {strategy_name}"
                        )
                        continue

                    results[strategy_name] = result
                    current_app.logger.info(
                        f"Crypto strategy {strategy_name} executed successfully"
                    )

                except Exception as e:
                    current_app.logger.error(
                        f"Error in crypto strategy {strategy_name}: {str(e)}"
                    )
                    results[strategy_name] = {"error": str(e)}

            return {
                "status": "success",
                "message": f"Crypto trading started with {len(strategy_names)} strategies",
                "results": results,
            }

        except Exception as e:
            current_app.logger.error(f"Failed to start crypto trading: {str(e)}")
            return {"status": "error", "message": str(e)}

    def stop_trading(self):
        """Stop crypto trading"""
        self.is_running = False

        # Update database status
        self._update_bot_status(is_running=False)

        current_app.logger.info("Crypto trading stopped")
        return {"status": "success", "message": "Crypto trading stopped"}

    def get_crypto_watchlist(self):
        """Get list of crypto symbols to trade"""
        try:
            # Get top crypto pairs from Binance
            top_cryptos = self.binance.get_top_crypto_symbols(limit=10)
            return [crypto["symbol"] for crypto in top_cryptos]
        except Exception as e:
            current_app.logger.error(f"Failed to get crypto watchlist: {str(e)}")
            # Fallback to popular crypto pairs
            return [
                "BTCUSDT",
                "ETHUSDT",
                "BNBUSDT",
                "ADAUSDT",
                "XRPUSDT",
                "SOLUSDT",
                "DOTUSDT",
                "DOGEUSDT",
                "AVAXUSDT",
                "MATICUSDT",
            ]

    def run_momentum_strategy(self, user_id, symbols, is_paper=True):
        """Crypto momentum trading strategy"""
        signals = []

        for symbol in symbols:
            try:
                # Get historical data
                df = self.binance.get_klines(symbol, interval="5m", limit=50)
                if df is None or len(df) < 20:
                    continue

                # Calculate momentum indicators
                df["sma_10"] = df["close"].rolling(window=10).mean()
                df["sma_20"] = df["close"].rolling(window=20).mean()
                df["rsi"] = self.calculate_rsi(df["close"])
                df["price_change"] = df["close"].pct_change()

                current_price = df["close"].iloc[-1]
                sma_10 = df["sma_10"].iloc[-1]
                sma_20 = df["sma_20"].iloc[-1]
                rsi = df["rsi"].iloc[-1]
                recent_momentum = df["price_change"].tail(5).mean()

                # Momentum signals
                if (
                    sma_10 > sma_20 and rsi < 70 and recent_momentum > 0.01
                ):  # 1% momentum
                    signal = self.generate_buy_signal(
                        user_id, symbol, current_price, "crypto_momentum", is_paper
                    )
                    if signal:
                        signals.append(signal)

                elif (
                    sma_10 < sma_20 and rsi > 30 and recent_momentum < -0.01
                ):  # -1% momentum
                    signal = self.generate_sell_signal(
                        user_id, symbol, current_price, "crypto_momentum", is_paper
                    )
                    if signal:
                        signals.append(signal)

            except Exception as e:
                current_app.logger.error(
                    f"Error processing {symbol} in momentum strategy: {str(e)}"
                )
                continue

        return {
            "strategy": "crypto_momentum",
            "signals": len(signals),
            "details": signals,
        }

    def run_mean_reversion_strategy(self, user_id, symbols, is_paper=True):
        """Crypto mean reversion strategy"""
        signals = []

        for symbol in symbols:
            try:
                # Get historical data
                df = self.binance.get_klines(symbol, interval="15m", limit=100)
                if df is None or len(df) < 50:
                    continue

                # Calculate mean reversion indicators
                df["sma_50"] = df["close"].rolling(window=50).mean()
                df["std_50"] = df["close"].rolling(window=50).std()
                df["upper_band"] = df["sma_50"] + (2 * df["std_50"])
                df["lower_band"] = df["sma_50"] - (2 * df["std_50"])
                df["rsi"] = self.calculate_rsi(df["close"])

                current_price = df["close"].iloc[-1]
                upper_band = df["upper_band"].iloc[-1]
                lower_band = df["lower_band"].iloc[-1]
                rsi = df["rsi"].iloc[-1]

                # Mean reversion signals
                if current_price <= lower_band and rsi < 30:  # Oversold
                    signal = self.generate_buy_signal(
                        user_id,
                        symbol,
                        current_price,
                        "crypto_mean_reversion",
                        is_paper,
                    )
                    if signal:
                        signals.append(signal)

                elif current_price >= upper_band and rsi > 70:  # Overbought
                    signal = self.generate_sell_signal(
                        user_id,
                        symbol,
                        current_price,
                        "crypto_mean_reversion",
                        is_paper,
                    )
                    if signal:
                        signals.append(signal)

            except Exception as e:
                current_app.logger.error(
                    f"Error processing {symbol} in mean reversion strategy: {str(e)}"
                )
                continue

        return {
            "strategy": "crypto_mean_reversion",
            "signals": len(signals),
            "details": signals,
        }

    def run_breakout_strategy(self, user_id, symbols, is_paper=True):
        """Crypto breakout strategy"""
        signals = []

        for symbol in symbols:
            try:
                # Get historical data
                df = self.binance.get_klines(
                    symbol, interval="1h", limit=24
                )  # 24 hours
                if df is None or len(df) < 20:
                    continue

                # Calculate breakout levels
                recent_high = df["high"].tail(20).max()
                recent_low = df["low"].tail(20).min()
                current_price = df["close"].iloc[-1]
                volume = df["volume"].iloc[-1]
                avg_volume = df["volume"].tail(10).mean()

                # Calculate price change
                price_change = (current_price - df["close"].iloc[-2]) / df[
                    "close"
                ].iloc[-2]

                # Breakout signals with volume confirmation
                if (
                    current_price > recent_high
                    and volume > avg_volume * 1.5
                    and price_change > 0.02
                ):  # 2% breakout
                    signal = self.generate_buy_signal(
                        user_id, symbol, current_price, "crypto_breakout", is_paper
                    )
                    if signal:
                        signals.append(signal)

                elif (
                    current_price < recent_low
                    and volume > avg_volume * 1.5
                    and price_change < -0.02
                ):  # -2% breakdown
                    signal = self.generate_sell_signal(
                        user_id, symbol, current_price, "crypto_breakout", is_paper
                    )
                    if signal:
                        signals.append(signal)

            except Exception as e:
                current_app.logger.error(
                    f"Error processing {symbol} in breakout strategy: {str(e)}"
                )
                continue

        return {
            "strategy": "crypto_breakout",
            "signals": len(signals),
            "details": signals,
        }

    def generate_buy_signal(self, user_id, symbol, price, strategy_name, is_paper=True):
        """Generate and execute buy signal for crypto"""
        try:
            # Calculate position size (risk 1% of account)
            quantity = self.calculate_crypto_position_size(symbol, price)
            if quantity <= 0:
                return None

            # Create order
            order = Order(
                user_id=user_id,
                symbol=symbol,
                exchange_type="crypto",
                quantity=quantity,
                order_type="market",
                side="buy",
                price=price,
                is_paper=is_paper,
            )

            if not is_paper:
                # Place real order on Binance
                order_payload = {
                    "symbol": symbol,
                    "side": "BUY",
                    "order_type": "MARKET",
                    "quantity": quantity,
                }

                exchange_order_id = self.binance.place_order(order_payload)
                order.exchange_order_id = exchange_order_id
                order.status = "filled"  # Market orders fill immediately
                order.filled_quantity = quantity
                order.filled_price = price
            else:
                # Paper trading
                order.status = "filled"
                order.filled_quantity = quantity
                order.filled_price = price

            db.session.add(order)
            db.session.commit()

            current_app.logger.info(
                f"Crypto BUY signal executed: {symbol} at {price} (Strategy: {strategy_name})"
            )

            return {
                "action": "BUY",
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "strategy": strategy_name,
                "order_id": order.id,
            }

        except Exception as e:
            current_app.logger.error(f"Failed to execute crypto buy signal: {str(e)}")
            return None

    def generate_sell_signal(
        self, user_id, symbol, price, strategy_name, is_paper=True
    ):
        """Generate and execute sell signal for crypto"""
        try:
            # For selling, we need to check if we have holdings
            # For now, use a fixed quantity (in real implementation, check portfolio)
            quantity = self.calculate_crypto_position_size(symbol, price)
            if quantity <= 0:
                return None

            # Create order
            order = Order(
                user_id=user_id,
                symbol=symbol,
                exchange_type="crypto",
                quantity=quantity,
                order_type="market",
                side="sell",
                price=price,
                is_paper=is_paper,
            )

            if not is_paper:
                # Place real order on Binance
                order_payload = {
                    "symbol": symbol,
                    "side": "SELL",
                    "order_type": "MARKET",
                    "quantity": quantity,
                }

                exchange_order_id = self.binance.place_order(order_payload)
                order.exchange_order_id = exchange_order_id
                order.status = "filled"
                order.filled_quantity = quantity
                order.filled_price = price
            else:
                # Paper trading
                order.status = "filled"
                order.filled_quantity = quantity
                order.filled_price = price

            db.session.add(order)
            db.session.commit()

            current_app.logger.info(
                f"Crypto SELL signal executed: {symbol} at {price} (Strategy: {strategy_name})"
            )

            return {
                "action": "SELL",
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "strategy": strategy_name,
                "order_id": order.id,
            }

        except Exception as e:
            current_app.logger.error(f"Failed to execute crypto sell signal: {str(e)}")
            return None

    def calculate_crypto_position_size(self, symbol, price):
        """Calculate appropriate position size for crypto trading"""
        try:
            # Risk 1% of account value (simplified calculation)
            # In real implementation, get account balance from Binance
            account_value = 1000  # Assume $1000 account
            risk_amount = account_value * 0.01  # 1% risk

            # Calculate quantity based on price
            quantity = risk_amount / price

            # Get symbol info for minimum quantity
            symbol_info = self.binance.get_symbol_info(symbol)
            if symbol_info:
                # Apply minimum quantity and step size filters
                min_qty = float(symbol_info["filters"][1]["minQty"])
                step_size = float(symbol_info["filters"][1]["stepSize"])

                # Round to valid step size
                quantity = max(min_qty, quantity)
                quantity = round(quantity / step_size) * step_size

            return quantity

        except Exception as e:
            current_app.logger.error(f"Error calculating position size: {str(e)}")
            return 0.001  # Fallback to small quantity

    def calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def get_portfolio_summary(self, user_id):
        """Get crypto portfolio summary"""
        try:
            if not self.binance.is_connected:
                return {"error": "Binance not connected"}

            balances = self.binance.get_balances()

            portfolio = []
            total_value = 0

            for balance in balances:
                if balance["total"] > 0:
                    # Get current price in USDT
                    symbol = f"{balance['asset']}USDT"
                    if balance["asset"] == "USDT":
                        price = 1.0
                        value = balance["total"]
                    else:
                        price = self.binance.get_price(symbol)
                        value = balance["total"] * price if price else 0

                    portfolio.append(
                        {
                            "asset": balance["asset"],
                            "quantity": balance["total"],
                            "price": price,
                            "value": value,
                        }
                    )

                    total_value += value

            return {
                "portfolio": portfolio,
                "total_value": total_value,
                "currency": "USDT",
            }

        except Exception as e:
            current_app.logger.error(f"Error getting crypto portfolio: {str(e)}")
            return {"error": str(e)}

    def get_trading_status(self):
        """Get current trading status and active strategies"""
        try:
            from datetime import datetime

            # Build active strategies data with mock trading sessions
            active_strategies = {}
            for strategy_name in self.active_strategies.keys():

                # Calculate strategy performance
                total_pnl = 0  # Simplified for now
                trades_count = 0

                # Create mock active positions for demo
                active_positions = []
                if self.is_running:
                    import random

                    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT"]

                    if random.choice([True, False]):  # 50% chance of active position
                        symbol = random.choice(symbols)
                        entry_price = random.uniform(100, 50000)
                        current_price = entry_price * random.uniform(0.98, 1.02)
                        quantity = random.uniform(0.001, 1.0)
                        unrealized_pnl = (current_price - entry_price) * quantity

                        active_positions.append(
                            {
                                "symbol": symbol,
                                "quantity": round(quantity, 6),
                                "entry_price": round(entry_price, 4),
                                "current_price": round(current_price, 4),
                                "unrealized_pnl": round(unrealized_pnl, 6),
                            }
                        )

                active_strategies[strategy_name] = {
                    "start_time": (
                        datetime.now().strftime("%H:%M UTC")
                        if self.is_running
                        else None
                    ),
                    "trades_count": trades_count,
                    "total_pnl": total_pnl,
                    "active_positions": active_positions,
                }

            return {
                "is_running": self.is_running,
                "active_strategies": active_strategies,
                "total_trades": len(active_strategies),
                "start_time": (
                    datetime.now().strftime("%H:%M UTC") if self.is_running else None
                ),
            }

        except Exception as e:
            current_app.logger.error(f"Error getting crypto trading status: {str(e)}")
            return {
                "is_running": False,
                "active_strategies": {},
                "total_trades": 0,
                "error": str(e),
            }

    def get_status(self):
        """Get bot status (for compatibility with bot manager)"""
        return {
            "is_running": self.is_running,
            "start_time": (
                datetime.now().strftime("%H:%M UTC") if self.is_running else None
            ),
            "total_trades": len(self.active_strategies),
            "positions": self.get_trading_status().get("active_strategies", {}),
        }

    def _update_bot_status(self, is_running=None, strategies=None):
        """Update bot status in database for persistence"""
        try:
            from ..models import TradingBotStatus
            from datetime import datetime

            bot_status = (
                TradingBotStatus.query.filter_by(
                    user_id=self.user_id, bot_type="crypto"
                )
                .with_for_update(nowait=False)
                .first()
            )
            if not bot_status:
                # Create then flush to honor unique constraint; handle race by catching IntegrityError
                bot_status = TradingBotStatus(user_id=self.user_id, bot_type="crypto")
                db.session.add(bot_status)
                try:
                    db.session.flush()
                except Exception as flush_err:
                    db.session.rollback()
                    # Re-query in case another session inserted simultaneously
                    bot_status = TradingBotStatus.query.filter_by(
                        user_id=self.user_id, bot_type="crypto"
                    ).first()
                    if not bot_status:
                        raise flush_err

            if is_running is not None:
                bot_status.is_running = is_running

                if is_running:
                    bot_status.started_at = datetime.utcnow()
                    bot_status.stopped_at = None
                else:
                    bot_status.stopped_at = datetime.utcnow()

            if strategies is not None:
                bot_status.strategies = strategies

            # Update heartbeat
            bot_status.last_heartbeat = datetime.utcnow()

            db.session.commit()
            current_app.logger.info(
                f"Updated crypto bot status in database: running={is_running}"
            )

        except Exception as e:
            current_app.logger.error(f"Error updating crypto bot status: {e}")
            db.session.rollback()
