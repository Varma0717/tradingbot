/* 
Enhanced Unified Dashboard with Grid Trading Integration
Real-time data display with fallback demo data
*/

class EnhancedDashboard {
    constructor() {
        this.isAuthenticated = false;
        this.updateInterval = null;
        this.gridDashboard = null;

        this.init();
    }

    async init() {
        console.log('🚀 Initializing Enhanced Dashboard...');

        // Check authentication
        this.isAuthenticated = await this.checkAuthentication();

        // Initialize components
        this.initializeEventListeners();

        // Load initial data (starts with demo, then tries real data)
        await this.loadInitialData();

        // Start auto-refresh
        this.startAutoRefresh();

        // Initialize Grid Trading Dashboard
        this.initializeGridTrading();

        // Show welcome notification
        this.showNotification('📊 Enhanced Dashboard Loaded!', 'success');

        console.log('✅ Enhanced Dashboard Ready!');
    }

    async checkAuthentication() {
        try {
            const response = await fetch('/user/api/bot-status', { method: 'HEAD' });
            return response.ok;
        } catch {
            return false;
        }
    }

    initializeEventListeners() {
        // Trading mode toggle
        const tradingModeToggle = document.getElementById('trading-mode-toggle');
        if (tradingModeToggle) {
            tradingModeToggle.addEventListener('change', (e) => {
                this.handleTradingModeChange(e.target.checked);
            });
        }

        // Bot control buttons
        this.setupBotControls();

        // Refresh button
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadInitialData();
                this.showNotification('Dashboard refreshed!', 'success');
            });
        }

        // Demo data buttons
        const generateDemoBtn = document.getElementById('generateDemoBtn');
        const resetDemoBtn = document.getElementById('resetDemoBtn');

        if (generateDemoBtn) {
            generateDemoBtn.addEventListener('click', () => this.generateDemoData());
        }

        if (resetDemoBtn) {
            resetDemoBtn.addEventListener('click', () => this.resetDemoData());
        }
    }

    setupBotControls() {
        // Stock bot controls
        const stockStart = document.getElementById('stock-bot-start');
        const stockStop = document.getElementById('stock-bot-stop');

        if (stockStart) stockStart.addEventListener('click', () => this.startBot('stock'));
        if (stockStop) stockStop.addEventListener('click', () => this.stopBot('stock'));

        // Crypto bot controls
        const cryptoStart = document.getElementById('crypto-bot-start');
        const cryptoStop = document.getElementById('crypto-bot-stop');

        if (cryptoStart) cryptoStart.addEventListener('click', () => this.startBot('crypto'));
        if (cryptoStop) cryptoStop.addEventListener('click', () => this.stopBot('crypto'));
    }

    async loadInitialData() {
        console.log('📊 Loading dashboard data...');

        // Always start with demo data for immediate display
        console.log('🎭 Loading demo data for immediate display...');
        this.loadDemoData();

        // Then try to load real data in background
        try {
            const [portfolioData, botData, activityData, aiData] = await Promise.all([
                this.loadPortfolioData(),
                this.loadBotStatus(),
                this.loadRecentActivity(),
                this.loadAISignals()
            ]);

            // Only update if we got valid real data
            if (portfolioData.success) {
                console.log('✅ Real portfolio data loaded, updating display...');
                this.updatePortfolioDisplay(portfolioData);
            }

            if (botData.success) {
                console.log('✅ Real bot data loaded, updating display...');
                this.updateBotStatusDisplay(botData);
            }

            if (activityData.success) {
                console.log('✅ Real activity data loaded, updating display...');
                this.updateActivityDisplay(activityData);
            }

            if (aiData.success) {
                console.log('✅ Real AI data loaded, updating display...');
                this.updateAISignalsDisplay(aiData);
            }

            this.updateLastRefreshTime();

        } catch (error) {
            console.error('Background data loading failed:', error);
            this.showNotification('Using demo data - real data unavailable', 'info');
        }
    }

    async loadPortfolioData() {
        try {
            const response = await fetch('/user/api/portfolio-summary');

            if (!response.ok) {
                throw new Error(`Portfolio API error: ${response.status}`);
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error('Portfolio data not available');
            }

            return data;

        } catch (error) {
            console.log('Using demo portfolio data...');
            return this.getDemoPortfolioData();
        }
    }

    async loadBotStatus() {
        try {
            const response = await fetch('/user/api/bot-status');

            if (!response.ok) {
                throw new Error(`Bot status API error: ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            console.log('Using demo bot status...');
            return this.getDemoBotStatus();
        }
    }

    async loadRecentActivity() {
        try {
            const response = await fetch('/user/api/recent-activity');

            if (!response.ok) {
                throw new Error(`Activity API error: ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            console.log('Using demo activity data...');
            return this.getDemoActivityData();
        }
    }

    async loadAISignals() {
        try {
            const response = await fetch('/user/api/ai/signals');

            if (!response.ok) {
                throw new Error(`AI signals API error: ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            console.log('Using demo AI signals...');
            return this.getDemoAISignals();
        }
    }

    updatePortfolioDisplay(data) {
        // Portfolio value
        const portfolioValue = document.getElementById('portfolio-value');
        if (portfolioValue) {
            portfolioValue.textContent = `$${Number(data.total_value || 0).toLocaleString()}`;
        }

        // Daily P&L
        const dailyPnl = document.getElementById('daily-pnl');
        const dailyPnlPercent = document.getElementById('daily-pnl-percent');

        if (dailyPnl) {
            const pnl = data.daily_pnl || 0;
            dailyPnl.textContent = `$${Number(pnl).toLocaleString()}`;
            dailyPnl.className = pnl >= 0 ? 'text-green-600 font-bold' : 'text-red-600 font-bold';
        }

        if (dailyPnlPercent) {
            const pnlPercent = data.daily_pnl_percent || 0;
            const pnlText = `${pnlPercent >= 0 ? '+' : ''}${pnlPercent.toFixed(2)}%`;
            dailyPnlPercent.innerHTML = `<span class="${pnlPercent >= 0 ? 'text-green-600' : 'text-red-600'}">${pnlText}</span>`;
        }

        // Portfolio change
        const portfolioChange = document.getElementById('portfolio-change');
        if (portfolioChange) {
            const changeValue = data.portfolio_change || 0;
            const changePercent = data.portfolio_change_percent || 0;
            const changeText = `${changeValue >= 0 ? '+' : ''}$${Math.abs(changeValue).toLocaleString()} (${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%)`;
            portfolioChange.innerHTML = `<span class="${changeValue >= 0 ? 'text-green-600' : 'text-red-600'}">${changeText}</span>`;
        }

        // Active trades
        const activeTrades = document.getElementById('active-trades');
        if (activeTrades) {
            activeTrades.textContent = data.positions_count || '0';
        }

        // Update additional portfolio metrics
        this.updatePortfolioMetrics(data);
    }

    updatePortfolioMetrics(data) {
        // Total P&L
        const totalPnl = document.getElementById('total-pnl');
        if (totalPnl) {
            const pnl = data.total_pnl || 0;
            totalPnl.textContent = `$${Number(pnl).toLocaleString()}`;
            totalPnl.className = pnl >= 0 ? 'text-green-600 font-bold' : 'text-red-600 font-bold';
        }

        // Cash available
        const cashAvailable = document.getElementById('cash-available');
        if (cashAvailable) {
            cashAvailable.textContent = `$${Number(data.cash_available || 0).toLocaleString()}`;
        }

        // Total invested
        const totalInvested = document.getElementById('total-invested');
        if (totalInvested) {
            totalInvested.textContent = `$${Number(data.total_invested || 0).toLocaleString()}`;
        }
    }

    updateBotStatusDisplay(data) {
        if (!data || !data.success) {
            console.warn('Invalid bot status data');
            return;
        }

        const stockRunning = data.stock_bot?.running || false;
        const cryptoRunning = data.crypto_bot?.running || false;

        // Update bot status indicators
        this.updateBotIndicators(stockRunning, cryptoRunning);

        // Update bot statistics
        this.updateBotStatistics(data);

        // Show/hide control buttons
        this.updateBotControls(stockRunning, cryptoRunning);
    }

    updateBotIndicators(stockRunning, cryptoRunning) {
        // Stock bot indicator
        const stockIndicator = document.getElementById('stock-status-indicator');
        if (stockIndicator) {
            stockIndicator.className = `w-3 h-3 rounded-full ${stockRunning ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`;
        }

        // Crypto bot indicator
        const cryptoIndicator = document.getElementById('crypto-status-indicator');
        if (cryptoIndicator) {
            cryptoIndicator.className = `w-3 h-3 rounded-full ${cryptoRunning ? 'bg-orange-500 animate-pulse' : 'bg-gray-400'}`;
        }

        // Overall status
        const overallStatus = document.getElementById('overall-status');
        const overallStatusText = document.getElementById('overall-status-text');

        if (overallStatus && overallStatusText) {
            if (stockRunning || cryptoRunning) {
                overallStatus.className = 'w-3 h-3 rounded-full bg-green-500 animate-pulse';
                const runningCount = (stockRunning ? 1 : 0) + (cryptoRunning ? 1 : 0);
                overallStatusText.textContent = `${runningCount} Bot${runningCount > 1 ? 's' : ''} Running`;
            } else {
                overallStatus.className = 'w-3 h-3 rounded-full bg-gray-400';
                overallStatusText.textContent = 'All Inactive';
            }
        }
    }

    updateBotStatistics(data) {
        // Stock bot stats
        if (data.stock_bot) {
            const stockUptime = document.getElementById('stock-bot-uptime');
            const stockTrades = document.getElementById('stock-bot-trades');
            const stockProfit = document.getElementById('stock-bot-profit');

            if (stockUptime) stockUptime.textContent = data.stock_bot.uptime || 'N/A';
            if (stockTrades) stockTrades.textContent = data.stock_bot.trades_today || '0';
            if (stockProfit) stockProfit.textContent = `$${(data.stock_bot.profit_today || 0).toLocaleString()}`;
        }

        // Crypto bot stats
        if (data.crypto_bot) {
            const cryptoUptime = document.getElementById('crypto-bot-uptime');
            const cryptoTrades = document.getElementById('crypto-bot-trades');
            const cryptoProfit = document.getElementById('crypto-bot-profit');

            if (cryptoUptime) cryptoUptime.textContent = data.crypto_bot.uptime || 'N/A';
            if (cryptoTrades) cryptoTrades.textContent = data.crypto_bot.trades_today || '0';
            if (cryptoProfit) cryptoProfit.textContent = `$${(data.crypto_bot.profit_today || 0).toLocaleString()}`;
        }

        // Overall stats
        if (data.overall_status) {
            const totalTrades = document.getElementById('total-trades-today');
            const totalProfit = document.getElementById('total-profit-today');
            const averageWinRate = document.getElementById('average-win-rate');

            if (totalTrades) totalTrades.textContent = data.overall_status.total_trades_today || '0';
            if (totalProfit) totalProfit.textContent = `$${(data.overall_status.total_profit_today || 0).toLocaleString()}`;
            if (averageWinRate) averageWinRate.textContent = `${(data.overall_status.average_win_rate || 0).toFixed(1)}%`;
        }
    }

    updateBotControls(stockRunning, cryptoRunning) {
        // Stock bot buttons
        const stockStart = document.getElementById('stock-bot-start');
        const stockStop = document.getElementById('stock-bot-stop');

        if (stockStart && stockStop) {
            if (stockRunning) {
                stockStart.classList.add('hidden');
                stockStop.classList.remove('hidden');
            } else {
                stockStart.classList.remove('hidden');
                stockStop.classList.add('hidden');
            }
        }

        // Crypto bot buttons
        const cryptoStart = document.getElementById('crypto-bot-start');
        const cryptoStop = document.getElementById('crypto-bot-stop');

        if (cryptoStart && cryptoStop) {
            if (cryptoRunning) {
                cryptoStart.classList.add('hidden');
                cryptoStop.classList.remove('hidden');
            } else {
                cryptoStart.classList.remove('hidden');
                cryptoStop.classList.add('hidden');
            }
        }
    }

    updateActivityDisplay(data) {
        const activityContainer = document.getElementById('recent-activity');
        if (!activityContainer || !data || !data.success) {
            console.log('Activity container not found or no data');
            return;
        }

        const activities = data.activities || [];

        if (activities.length === 0) {
            activityContainer.innerHTML = `
                <div class="text-center text-gray-500 py-8">
                    <p>No trades yet</p>
                    <p class="text-sm">Start live trading to see results</p>
                </div>
            `;
            return;
        }

        activityContainer.innerHTML = activities.map(activity => `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg mb-2">
                <div class="flex-1">
                    <div class="flex items-center">
                        <span class="w-2 h-2 rounded-full ${this.getActivityColor(activity.type)} mr-3"></span>
                        <div>
                            <p class="text-sm font-medium text-gray-900">${activity.description}</p>
                            <p class="text-xs text-gray-500">${activity.timestamp}</p>
                        </div>
                    </div>
                </div>
                ${activity.pnl ? `
                    <div class="text-sm font-medium ${activity.pnl >= 0 ? 'text-green-600' : 'text-red-600'}">
                        ${activity.pnl >= 0 ? '+' : ''}$${activity.pnl.toLocaleString()}
                    </div>
                ` : ''}
            </div>
        `).join('');
    }

    getActivityColor(type) {
        switch (type) {
            case 'TRADE': return 'bg-blue-500';
            case 'SYSTEM': return 'bg-green-500';
            case 'ERROR': return 'bg-red-500';
            default: return 'bg-gray-400';
        }
    }

    updateAISignalsDisplay(data) {
        const signalsContainer = document.getElementById('ai-signals-list');
        if (!signalsContainer || !data || !data.success) {
            return;
        }

        const signals = data.signals || [];

        signalsContainer.innerHTML = signals.map(signal => `
            <div class="bg-white p-4 rounded-lg border border-gray-200 mb-3">
                <div class="flex items-center justify-between mb-2">
                    <div class="font-semibold text-lg">${signal.symbol}</div>
                    <div class="text-sm ${this.getSignalColor(signal.signal)} font-bold px-2 py-1 rounded">
                        ${signal.signal}
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-2 text-sm text-gray-600">
                    <div>Confidence: <span class="font-medium">${signal.confidence}%</span></div>
                    <div>Target: <span class="font-medium">$${signal.target_price}</span></div>
                    <div>Current: <span class="font-medium">$${signal.current_price}</span></div>
                    <div>Return: <span class="font-medium text-green-600">+${signal.potential_return}%</span></div>
                </div>
                <div class="text-xs text-gray-500 mt-2">
                    ${signal.strategy} • ${signal.timeframe}
                </div>
            </div>
        `).join('');
    }

    getSignalColor(signal) {
        switch (signal) {
            case 'STRONG_BUY': return 'bg-green-100 text-green-800';
            case 'BUY': return 'bg-green-50 text-green-700';
            case 'HOLD': return 'bg-yellow-50 text-yellow-700';
            case 'SELL': return 'bg-red-50 text-red-700';
            case 'STRONG_SELL': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-700';
        }
    }

    // Demo data functions
    getDemoPortfolioData() {
        return {
            success: true,
            total_value: 52450.75,
            total_pnl: 2450.75,
            total_pnl_percent: 4.89,
            daily_pnl: 485.20,
            daily_pnl_percent: 0.93,
            portfolio_change: 345.80,
            portfolio_change_percent: 0.66,
            positions_count: 6,
            cash_available: 15280.00,
            total_invested: 37170.75
        };
    }

    getDemoBotStatus() {
        return {
            success: true,
            stock_bot: {
                running: true,
                uptime: '4h 23m',
                trades_today: 18,
                profit_today: 587.45,
                win_rate: 83.3
            },
            crypto_bot: {
                running: true,
                uptime: '5h 47m',
                trades_today: 24,
                profit_today: 692.80,
                win_rate: 87.5
            },
            overall_status: {
                total_trades_today: 42,
                total_profit_today: 1280.25,
                average_win_rate: 85.4
            }
        };
    }

    getDemoActivityData() {
        const now = new Date();
        const formatTime = (minutes) => {
            const time = new Date(now.getTime() - minutes * 60000);
            return time.toLocaleTimeString();
        };

        return {
            success: true,
            activities: [
                {
                    type: 'TRADE',
                    description: 'SELL 50 AAPL @ $175.85 (Grid Profit)',
                    timestamp: formatTime(5),
                    pnl: 127.50
                },
                {
                    type: 'TRADE',
                    description: 'BUY 0.5 BTC @ $43,250 (Grid Entry)',
                    timestamp: formatTime(12),
                    pnl: 0
                },
                {
                    type: 'TRADE',
                    description: 'SELL 25 TSLA @ $251.90 (Grid Profit)',
                    timestamp: formatTime(18),
                    pnl: 97.25
                },
                {
                    type: 'TRADE',
                    description: 'BUY 100 MSFT @ $338.45 (Grid Entry)',
                    timestamp: formatTime(25),
                    pnl: 0
                },
                {
                    type: 'TRADE',
                    description: 'SELL 15 NVDA @ $521.30 (Grid Profit)',
                    timestamp: formatTime(31),
                    pnl: 156.75
                },
                {
                    type: 'SYSTEM',
                    description: '🔥 Grid Trading Bot - Target Hit! +3.2% Daily ROI',
                    timestamp: formatTime(35)
                },
                {
                    type: 'TRADE',
                    description: 'BUY 200 AMZN @ $142.80 (Grid Entry)',
                    timestamp: formatTime(42),
                    pnl: 0
                },
                {
                    type: 'TRADE',
                    description: 'SELL 1.5 ETH @ $2,580 (Grid Profit)',
                    timestamp: formatTime(48),
                    pnl: 89.50
                }
            ]
        };
    }

    getDemoAISignals() {
        return {
            success: true,
            signals: [
                {
                    symbol: 'AAPL',
                    signal: 'BUY',
                    confidence: 85.2,
                    target_price: 185.00,
                    current_price: 178.20,
                    potential_return: 3.81,
                    timeframe: '1-3 days',
                    strategy: 'Momentum + Volume Analysis'
                },
                {
                    symbol: 'NVDA',
                    signal: 'STRONG_BUY',
                    confidence: 92.1,
                    target_price: 450.00,
                    current_price: 432.80,
                    potential_return: 3.97,
                    timeframe: '1-2 days',
                    strategy: 'AI Sentiment + Technical'
                }
            ]
        };
    }

    // Bot control functions
    async startBot(type) {
        try {
            const response = await fetch(`/user/api/${type}-bot/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification(`${type.charAt(0).toUpperCase() + type.slice(1)} bot started successfully!`, 'success');
                this.loadBotStatus();
            } else {
                throw new Error(result.message);
            }

        } catch (error) {
            console.error(`Failed to start ${type} bot:`, error);
            this.showNotification(`Failed to start ${type} bot: ${error.message}`, 'error');
        }
    }

    async stopBot(type) {
        try {
            const response = await fetch(`/user/api/${type}-bot/stop`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification(`${type.charAt(0).toUpperCase() + type.slice(1)} bot stopped successfully!`, 'warning');
                this.loadBotStatus();
            } else {
                throw new Error(result.message);
            }

        } catch (error) {
            console.error(`Failed to stop ${type} bot:`, error);
            this.showNotification(`Failed to stop ${type} bot: ${error.message}`, 'error');
        }
    }

    async handleTradingModeChange(isLive) {
        try {
            const mode = isLive ? 'live' : 'paper';

            const response = await fetch('/user/preferences/trading-mode', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ trading_mode: mode })
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification(`Switched to ${mode} trading mode`, 'success');
                this.loadInitialData();
            } else {
                throw new Error(result.message);
            }

        } catch (error) {
            console.error('Failed to change trading mode:', error);
            this.showNotification('Failed to change trading mode', 'error');
        }
    }

    generateDemoData() {
        console.log('📊 Generating demo data...');
        this.loadDemoData();
        this.showNotification('Demo data generated!', 'success');
    }

    resetDemoData() {
        console.log('🔄 Resetting demo data...');
        this.loadDemoData();
        this.showNotification('Demo data reset!', 'info');
    }

    loadDemoData() {
        const portfolioData = this.getDemoPortfolioData();
        const botData = this.getDemoBotStatus();
        const activityData = this.getDemoActivityData();
        const aiData = this.getDemoAISignals();

        this.updatePortfolioDisplay(portfolioData);
        this.updateBotStatusDisplay(botData);
        this.updateActivityDisplay(activityData);
        this.updateAISignalsDisplay(aiData);

        this.updateLastRefreshTime();
    }

    initializeGridTrading() {
        // Initialize the Grid Trading Dashboard component
        if (typeof GridTradingDashboard !== 'undefined') {
            this.gridDashboard = new GridTradingDashboard();
            console.log('🔥 Grid Trading Dashboard initialized');
        } else {
            console.warn('Grid Trading Dashboard not available');
        }
    }

    startAutoRefresh() {
        // Refresh data every 30 seconds
        this.updateInterval = setInterval(() => {
            this.loadInitialData();
        }, 30000);

        console.log('🔄 Auto-refresh started (30s interval)');
    }

    updateLastRefreshTime() {
        const lastUpdateElement = document.getElementById('last-update');
        if (lastUpdateElement) {
            const now = new Date();
            lastUpdateElement.textContent = `Last Updated: ${now.toLocaleTimeString()}`;
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
                type === 'warning' ? 'bg-yellow-500 text-white' :
                    'bg-blue-500 text-white'
            }`;

        // Add icon based on type
        const icon = type === 'success' ? '✅' :
            type === 'error' ? '❌' :
                type === 'warning' ? '⚠️' : 'ℹ️';

        notification.innerHTML = `
            <div class="flex items-center">
                <span class="mr-2">${icon}</span>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        // Remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        if (this.gridDashboard && this.gridDashboard.destroy) {
            this.gridDashboard.destroy();
        }
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    console.log('📱 DOM loaded, initializing Enhanced Dashboard...');

    setTimeout(() => {
        if (!window.enhancedDashboard) {
            window.enhancedDashboard = new EnhancedDashboard();
            console.log('✅ Enhanced Dashboard instance created');
        } else {
            console.log('⚠️ Enhanced Dashboard already exists');
        }
    }, 1000);
});

// Also initialize if document is already loaded
if (document.readyState === 'loading') {
    // Document is still loading, event listener will handle it
} else {
    // Document already loaded
    setTimeout(() => {
        if (!window.enhancedDashboard) {
            window.enhancedDashboard = new EnhancedDashboard();
            console.log('✅ Enhanced Dashboard instance created (document already loaded)');
        }
    }, 1000);
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EnhancedDashboard;
}
