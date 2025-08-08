// Trading Bot Dashboard JavaScript
// Handles real-time updates and trading mode switching

class TradingDashboard {
    constructor() {
        this.currentMode = 'paper'; // Default to paper trading
        this.isConnected = false;
        this.updateInterval = null;
        this.websocket = null;

        // Initialize dashboard
        this.init();
    }

    init() {
        console.log('🚀 Initializing Trading Dashboard...');

        // Load initial data
        this.loadTradingMode();
        this.loadDashboardData();

        // Setup event listeners
        this.setupEventListeners();

        // Start periodic updates
        this.startPeriodicUpdates();

        // Setup WebSocket connection
        this.setupWebSocket();

        console.log('✅ Dashboard initialized');
    }

    setupEventListeners() {
        // Mode switching buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="switch-to-paper"]')) {
                this.switchTradingMode('paper');
            } else if (e.target.matches('[data-action="switch-to-real"]')) {
                this.switchTradingMode('real');
            } else if (e.target.matches('#start-btn')) {
                this.startTrading();
            } else if (e.target.matches('#stop-btn')) {
                this.stopTrading();
            } else if (e.target.matches('[data-action="refresh"]')) {
                this.loadDashboardData();
            }
        });

        // Global functions for template compatibility
        window.switchToPaperTrading = () => this.switchTradingMode('paper');
        window.switchToRealTrading = () => this.switchTradingMode('real');
        window.loadDashboardData = () => this.loadDashboardData();
    }

    async loadTradingMode() {
        try {
            const response = await fetch('/api/mode');
            const result = await response.json();

            if (result.success) {
                this.currentMode = result.data.mode;
                this.updateModeDisplay(result.data);
                console.log(`📊 Current trading mode: ${this.currentMode}`);
            } else {
                console.error('Failed to load trading mode:', result.error);
                this.showError('Failed to load trading mode');
            }
        } catch (error) {
            console.error('Error loading trading mode:', error);
            this.showError('Network error while loading trading mode');
        }
    }

    async switchTradingMode(newMode) {
        try {
            // Show confirmation for real trading
            if (newMode === 'real') {
                const confirmed = confirm(
                    '⚠️ WARNING: You are about to switch to REAL MONEY trading!\\n\\n' +
                    'This will use your actual Binance account and real funds.\\n' +
                    'Are you absolutely sure you want to continue?'
                );

                if (!confirmed) {
                    return;
                }
            }

            this.showLoading('Switching trading mode...');

            const response = await fetch('/api/mode/switch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ mode: newMode })
            });

            const result = await response.json();

            if (result.success) {
                this.currentMode = result.current_mode;
                this.showSuccess(result.message);

                // Update dashboard data instead of reloading
                this.loadDashboardData();
            } else {
                this.showError(result.error || 'Failed to switch trading mode');
            }
        } catch (error) {
            console.error('Error switching trading mode:', error);
            this.showError('Network error while switching modes');
        } finally {
            this.hideLoading();
        }
    }

    async startTrading() {
        try {
            // Check if already starting/running
            const startBtn = document.getElementById('start-btn');
            if (startBtn && startBtn.disabled) {
                console.log('Start trading already in progress, ignoring request');
                return;
            }

            // Disable button to prevent multiple clicks
            if (startBtn) {
                startBtn.disabled = true;
                startBtn.textContent = 'Starting...';
            }

            this.showLoading('Starting trading...');

            const response = await fetch('/api/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess(result.message);
                this.loadDashboardData(); // Refresh data
            } else {
                this.showError(result.error || 'Failed to start trading');
            }
        } catch (error) {
            console.error('Error starting trading:', error);
            this.showError('Network error while starting trading');
        } finally {
            this.hideLoading();

            // Re-enable button after a delay
            setTimeout(() => {
                const startBtn = document.getElementById('start-btn');
                if (startBtn) {
                    startBtn.disabled = false;
                    startBtn.textContent = 'Start Trading';
                }
            }, 2000); // 2 second delay before allowing another start
        }
    }

    async stopTrading() {
        try {
            this.showLoading('Stopping trading...');

            const response = await fetch('/api/stop', {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess(result.message);
                this.loadDashboardData(); // Refresh data
            } else {
                this.showError(result.error || 'Failed to stop trading');
            }
        } catch (error) {
            console.error('Error stopping trading:', error);
            this.showError('Network error while stopping trading');
        } finally {
            this.hideLoading();
        }
    }

    async loadDashboardData() {
        try {
            const response = await fetch('/api/dashboard-data');
            const result = await response.json();

            if (result.success) {
                this.updateDashboard(result.data);
                this.isConnected = true;
            } else {
                console.error('Failed to load dashboard data:', result.error);
                this.showError('Failed to load dashboard data');
                this.isConnected = false;
            }
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.isConnected = false;
        }

        this.updateConnectionStatus();
    }

    updateDashboard(data) {
        // Update mode display
        if (data.mode) {
            this.updateModeDisplay(data.mode);
        }

        // Update bot status
        if (data.status) {
            this.updateBotStatus(data.status);
        }

        // Update balance
        if (data.summary) {
            this.updateBalance(data.summary.balance);
            this.updateMetrics(data.summary);
        }

        // Update trades
        if (data.trades) {
            this.updateTrades(data.trades);
        }

        // Update orders
        if (data.orders) {
            this.updateOrders(data.orders);
        }
    }

    updateModeDisplay(modeData) {
        const isReal = modeData.is_real_trading;

        // Update mode badges
        const modeBadges = document.querySelectorAll('[data-mode-badge]');
        modeBadges.forEach(badge => {
            badge.textContent = isReal ? 'REAL TRADING' : 'PAPER TRADING';
            badge.className = `badge ${isReal ? 'bg-danger' : 'bg-secondary'} ms-2`;
        });

        // Update mode alerts
        const alerts = document.querySelectorAll('[data-mode-alert]');
        alerts.forEach(alert => {
            if (isReal) {
                alert.className = 'alert alert-warning border-0 shadow-sm mb-4';
                alert.innerHTML = `
                    <div class="d-flex align-items-center">
                        <i class="bi bi-exclamation-triangle-fill fs-4 me-3 text-warning"></i>
                        <div>
                            <h6 class="mb-1">🚨 REAL MONEY TRADING ACTIVE</h6>
                            <small>All trades and profits affect your actual Binance account. Monitor carefully!</small>
                        </div>
                        <span class="badge bg-danger ms-auto">LIVE</span>
                    </div>
                `;
            } else {
                alert.className = 'alert alert-info border-0 shadow-sm mb-4';
                alert.innerHTML = `
                    <div class="d-flex align-items-center">
                        <i class="bi bi-info-circle-fill fs-4 me-3 text-info"></i>
                        <div>
                            <h6 class="mb-1">📊 PAPER TRADING MODE</h6>
                            <small>All trades are simulated. No real money is being used.</small>
                        </div>
                        <span class="badge bg-info ms-auto">SIMULATION</span>
                    </div>
                `;
            }
        });

        // Update switch buttons
        const switchButtons = document.querySelectorAll('[data-mode-switch]');
        switchButtons.forEach(container => {
            if (isReal) {
                container.innerHTML = `
                    <button class="btn btn-warning btn-sm me-2" data-action="switch-to-paper">
                        <i class="bi bi-shield-check me-1"></i>
                        Switch to Paper Trading
                    </button>
                `;
            } else {
                container.innerHTML = `
                    <button class="btn btn-success btn-sm me-2" data-action="switch-to-real">
                        <i class="bi bi-currency-dollar me-1"></i>
                        Switch to Real Trading
                    </button>
                `;
            }
        });
    }

    updateBotStatus(status) {
        const statusElement = document.getElementById('bot-status');
        if (statusElement) {
            const isRunning = status.is_running || status.status === 'active';
            statusElement.textContent = isRunning ? 'Running' : 'Stopped';
            statusElement.className = `metric-value ${isRunning ? 'status-running' : 'status-stopped'}`;
        }
    }

    updateBalance(balance) {
        const balanceElement = document.getElementById('balance');
        if (balanceElement) {
            balanceElement.textContent = `$${(balance || 0).toFixed(2)}`;
        }
    }

    updateMetrics(metrics) {
        // Update various metric displays
        const elements = {
            'total-trades': metrics.trades_count || 0,
            'active-orders': metrics.active_orders || 0,
            'profit-loss': `$${(metrics.profit || 0).toFixed(2)}`,
            'win-rate': `${(metrics.win_rate || 0).toFixed(1)}%`
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }

    updateTrades(tradesData) {
        // Update trades table/list if it exists
        const tradesContainer = document.getElementById('trades-container');
        if (tradesContainer && tradesData.recent) {
            // Implementation for trades display
            console.log('Updating trades:', tradesData.recent.length);
        }
    }

    updateOrders(ordersData) {
        // Update orders table/list if it exists
        const ordersContainer = document.getElementById('orders-container');
        if (ordersContainer && ordersData.list) {
            // Implementation for orders display
            console.log('Updating orders:', ordersData.list.length);
        }
    }

    startPeriodicUpdates() {
        // Update every 10 seconds
        this.updateInterval = setInterval(() => {
            this.loadDashboardData();
        }, 10000);
    }

    stopPeriodicUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    setupWebSocket() {
        try {
            // Don't create multiple WebSocket connections
            if (this.websocket && this.websocket.readyState === WebSocket.CONNECTING) {
                console.log('WebSocket already connecting, skipping...');
                return;
            }

            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                console.log('WebSocket already connected, skipping...');
                return;
            }

            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/realtime`;

            this.websocket = new WebSocket(wsUrl);

            this.websocket.onopen = () => {
                console.log('🔌 WebSocket connected');
                this.isConnected = true;
            };

            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            this.websocket.onclose = () => {
                console.log('🔌 WebSocket disconnected');
                this.isConnected = false;
                // Reconnect after 10 seconds (increased from 5 to reduce frequency)
                setTimeout(() => {
                    if (!this.isConnected) {
                        this.setupWebSocket();
                    }
                }, 10000);
            };

            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.isConnected = false;
            };
        } catch (error) {
            console.error('Failed to setup WebSocket:', error);
        }
    }

    handleWebSocketMessage(data) {
        if (data.type === 'periodic_update' && data.data) {
            this.updateDashboard(data.data);
        }
    }

    updateConnectionStatus() {
        const statusIndicator = document.getElementById('connection-status');
        if (statusIndicator) {
            statusIndicator.className = this.isConnected ? 'text-success' : 'text-danger';
            statusIndicator.textContent = this.isConnected ? 'Connected' : 'Disconnected';
        }
    }

    showLoading(message = 'Loading...') {
        // Show loading indicator
        const loader = document.getElementById('loading-indicator');
        if (loader) {
            loader.textContent = message;
            loader.style.display = 'block';
        }
    }

    hideLoading() {
        const loader = document.getElementById('loading-indicator');
        if (loader) {
            loader.style.display = 'none';
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';

        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);

        console.log(`${type.toUpperCase()}: ${message}`);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Prevent multiple dashboard instances
    if (window.tradingDashboard) {
        console.log('Dashboard already exists, skipping initialization');
        return;
    }

    console.log('Creating new trading dashboard instance');
    window.tradingDashboard = new TradingDashboard();
});

// Expose global functions for backward compatibility
window.switchToPaperTrading = () => {
    if (window.tradingDashboard) {
        window.tradingDashboard.switchTradingMode('paper');
    }
};

window.switchToRealTrading = () => {
    if (window.tradingDashboard) {
        window.tradingDashboard.switchTradingMode('real');
    }
};

window.loadDashboardData = () => {
    if (window.tradingDashboard) {
        window.tradingDashboard.loadDashboardData();
    }
};
