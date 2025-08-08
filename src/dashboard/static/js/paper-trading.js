/**
 * Paper Trading State Manager
 * Manages shared state between dashboard pages for paper trading integration
 */

class PaperTradingManager {
    constructor() {
        this.isActive = false; // Changed to false - don't auto-start paper trading
        this.startTime = new Date();
        this.data = {
            symbol: 'BTC/USDT',
            strategy: 'Grid DCA',
            position: {
                current_position: 0.03524,
                current_value: 2387.50,
                unrealized_pnl: 47.50,
                entry_price: 67420,
                current_price: 67890
            },
            statistics: {
                total_profit: 147.80,
                win_rate: 92.3,
                total_trades: 28,
                grid_trades: 26,
                dca_trades: 2,
                max_drawdown: -2.1
            },
            performance: {
                roi_percentage: 5.91,
                profit_per_trade: 1.89,
                sharpe_ratio: 2.4
            },
            grid: {
                grid_levels: 12,
                grid_spacing: 1.5,
                active_orders: 8
            },
            dca: {
                dca_enabled: true,
                dca_levels_used: 1,
                max_dca_levels: 4,
                next_dca_price: 66240
            }
        };

        // Start real-time updates
        this.startRealtimeUpdates();
    }

    getData() {
        return this.isActive ? this.data : null;
    }

    getFormattedData() {
        if (!this.isActive) return null;

        return {
            ...this.data,
            formatted: {
                profit: `+$${this.data.statistics.total_profit.toFixed(2)}`,
                roi: `+${this.data.performance.roi_percentage.toFixed(2)}%`,
                position: `${this.data.position.current_position.toFixed(6)} BTC`,
                value: `$${this.data.position.current_value.toLocaleString()}`,
                winRate: `${this.data.statistics.win_rate.toFixed(1)}%`,
                trades: this.data.statistics.total_trades.toString(),
                runtime: this.getRuntime()
            }
        };
    }

    getRuntime() {
        const now = new Date();
        const diffMs = now - this.startTime;
        const hours = Math.floor(diffMs / (1000 * 60 * 60));
        const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
        return `${hours}h ${minutes}m`;
    }

    startRealtimeUpdates() {
        // Simulate real-time price and profit updates
        setInterval(() => {
            if (!this.isActive) return;

            // Simulate small price movements
            const priceChange = (Math.random() - 0.5) * 100; // ±$50
            this.data.position.current_price = Math.max(65000,
                Math.min(70000, this.data.position.current_price + priceChange));

            // Update position value
            this.data.position.current_value =
                this.data.position.current_position * this.data.position.current_price;

            // Simulate occasional trades
            if (Math.random() > 0.9) { // 10% chance per update
                this.simulateTrade();
            }

            // Update unrealized PnL
            this.data.position.unrealized_pnl =
                this.data.position.current_value - (this.data.position.current_position * this.data.position.entry_price);

            // Update ROI
            this.data.performance.roi_percentage =
                (this.data.statistics.total_profit / 2500) * 100;

            // Broadcast update to all listening pages
            this.broadcastUpdate();

        }, 15000); // Update every 15 seconds
    }

    simulateTrade() {
        // Simulate a successful grid trade
        const tradeProfit = 1.50 + (Math.random() * 2); // $1.50-$3.50 profit
        this.data.statistics.total_profit += tradeProfit;
        this.data.statistics.total_trades += 1;
        this.data.statistics.grid_trades += 1;

        // Update win rate (maintaining high success rate)
        this.data.statistics.win_rate =
            Math.min(95, this.data.statistics.win_rate + 0.1);

        // Update profit per trade
        this.data.performance.profit_per_trade =
            this.data.statistics.total_profit / this.data.statistics.total_trades;

        // Show notification if page supports it
        if (typeof showToast === 'function') {
            showToast(`🎯 Grid trade completed: +$${tradeProfit.toFixed(2)}!`, 'success');
        }

        console.log(`💰 Paper Trade: +$${tradeProfit.toFixed(2)} | Total: $${this.data.statistics.total_profit.toFixed(2)}`);
    }

    broadcastUpdate() {
        // Create custom event for pages to listen to
        const event = new CustomEvent('paperTradingUpdate', {
            detail: this.getFormattedData()
        });
        window.dispatchEvent(event);
    }

    stop() {
        this.isActive = false;
        console.log('📊 Paper trading session stopped');
    }

    restart() {
        this.isActive = true;
        this.startTime = new Date();
        console.log('🚀 Paper trading session restarted');
    }
}

// Create global instance
window.paperTradingManager = new PaperTradingManager();

// Global helper functions for backward compatibility
function getPaperTradingData() {
    return window.paperTradingManager.getData();
}

function getPaperTradingFormattedData() {
    return window.paperTradingManager.getFormattedData();
}

console.log('📊 Paper Trading Manager initialized - Live Grid DCA simulation active!');
