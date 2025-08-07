/**
 * Trading Bot Dashboard - Main JavaScript File
 * Handles WebSocket connections, UI interactions, and utility functions
 */

// === GLOBAL VARIABLES ===
let ws = null;
let reconnectInterval = null;
let dataRefreshInterval = null;

// === INITIALIZATION ===
document.addEventListener('DOMContentLoaded', function () {
    console.log('Dashboard initialized');

    // Initialize Bootstrap components
    initializeBootstrapComponents();

    // Initialize WebSocket connection
    connectWebSocket();

    // Load initial data
    loadAllData();

    // Set up auto-refresh
    setupAutoRefresh();

    // Setup page-specific functionality
    setupPageSpecificFeatures();
});

// === BOOTSTRAP INITIALIZATION ===
function initializeBootstrapComponents() {
    try {
        // Initialize all dropdowns
        const dropdownElements = document.querySelectorAll('[data-bs-toggle="dropdown"]');
        dropdownElements.forEach(dropdownToggle => {
            if (typeof bootstrap !== 'undefined' && bootstrap.Dropdown) {
                new bootstrap.Dropdown(dropdownToggle);
            }
        });

        // Initialize tooltips if any
        const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipElements.forEach(tooltipElement => {
            if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
                new bootstrap.Tooltip(tooltipElement);
            }
        });

        console.log('Bootstrap components initialized');
    } catch (error) {
        console.error('Error initializing Bootstrap components:', error);
    }
}

// === DATA LOADING FUNCTIONS ===
function loadAllData() {
    const currentPage = getCurrentPage();

    // Load common data for all pages
    loadBotStatus();

    // Load page-specific data
    switch (currentPage) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'portfolio':
            loadPortfolioData();
            break;
        case 'trades':
            loadTradesData();
            break;
        case 'strategies':
            loadStrategiesData();
            break;
        case 'grid-dca':
            loadGridDcaData();
            break;
    }
}

function getCurrentPage() {
    const path = window.location.pathname;
    if (path === '/' || path === '/dashboard') return 'dashboard';
    if (path.includes('portfolio')) return 'portfolio';
    if (path.includes('trades')) return 'trades';
    if (path.includes('strategies')) return 'strategies';
    if (path.includes('grid-dca')) return 'grid-dca';
    return 'dashboard';
}

function setupAutoRefresh() {
    // Refresh data every 30 seconds
    dataRefreshInterval = setInterval(loadAllData, 30000);
}

function loadBotStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            updateBotStatus(data);
        })
        .catch(error => {
            console.error('Error loading bot status:', error);
        });
}

function updateBotStatus(data) {
    const statusElement = document.getElementById('botStatus');
    if (statusElement && data.success) {
        const status = data.bot_running ? 'running' : 'stopped';
        const statusClass = data.bot_running ? 'status-running' : 'status-stopped';
        const icon = data.bot_running ? 'bi-play-circle-fill' : 'bi-stop-circle-fill';

        statusElement.innerHTML = `
            <span class="${statusClass}">
                <i class="bi ${icon}"></i> ${status.charAt(0).toUpperCase() + status.slice(1)}
            </span>
        `;
    }
}

function loadDashboardData() {
    // Load dashboard-specific data
    loadPortfolioData();
    loadRecentTrades();
}

function loadPortfolioData() {
    fetch('/api/portfolio')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updatePortfolioDisplay(data);
            }
        })
        .catch(error => {
            console.error('Error loading portfolio data:', error);
        });
}

function updatePortfolioDisplay(data) {
    // Update portfolio balance
    updateElement('portfolioBalance', formatCurrency(data.total_value));
    updateElement('portfolioValue', formatCurrency(data.total_value));

    // Update P&L
    updateElement('totalPnl', formatCurrency(data.total_pnl));
    updateElement('totalPnlPercent', formatPercentage(data.total_pnl_percent));

    // Update daily P&L
    updateElement('dailyPnl', formatCurrency(data.daily_pnl));
    updateElement('dailyPnlPercent', formatPercentage(data.daily_pnl_percent));

    // Update positions
    updateElement('activePositions', data.active_positions);
    updateElement('totalAssets', `${data.total_assets} Assets`);

    // Update portfolio change indicators
    updateChangeIndicator('portfolioChange', data.total_pnl_percent);
    updateChangeIndicator('totalPnLChange', data.total_pnl_percent);
    updateChangeIndicator('dailyPnlPercent', data.daily_pnl_percent);
}

function loadTradesData() {
    fetch('/api/trades')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateTradesDisplay(data);
            }
        })
        .catch(error => {
            console.error('Error loading trades data:', error);
        });
}

function updateTradesDisplay(data) {
    const stats = data.stats;

    // Update trade metrics
    updateElement('totalTrades', stats.total_trades);
    updateElement('todayTrades', `${stats.today_trades} Today`);
    updateElement('winRate', formatPercentage(stats.win_rate));
    updateElement('winRateChange', formatPercentage(stats.win_rate_change, true));
    updateElement('totalPnL', formatCurrency(stats.total_pnl));
    updateElement('totalPnLChange', formatPercentage(stats.total_pnl_percent, true));
    updateElement('avgTradeSize', formatCurrency(stats.avg_trade_size));
    updateElement('maxTradeSize', `Max: ${formatCurrency(stats.max_trade_size)}`);

    // Update recent trades table
    updateRecentTradesTable(data.recent_trades);
}

function loadStrategiesData() {
    fetch('/api/strategies')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateStrategiesDisplay(data);
            }
        })
        .catch(error => {
            console.error('Error loading strategies data:', error);
        });
}

function updateStrategiesDisplay(data) {
    const stats = data.stats;

    // Update strategy metrics
    updateElement('activeStrategies', stats.active_strategies);
    updateElement('totalStrategies', `${stats.total_strategies} Total`);
    updateElement('bestStrategy', stats.best_strategy);
    updateElement('bestPerformance', formatPercentage(stats.best_performance, true));
    updateElement('totalStrategyPnL', formatCurrency(stats.total_strategy_pnl));
    updateElement('strategyPnLChange', formatPercentage(stats.strategy_pnl_change, true));
    updateElement('avgWinRate', formatPercentage(stats.avg_win_rate));
    updateElement('winRateRange', stats.win_rate_range);

    // Update strategies table
    updateStrategiesTable(data.strategies);
}

function loadGridDcaData() {
    fetch('/api/grid-dca')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateGridDcaDisplay(data);
            }
        })
        .catch(error => {
            console.error('Error loading grid-dca data:', error);
        });
}

function updateGridDcaDisplay(data) {
    // Update strategy status
    updateElement('strategyStatus', `<span class="badge bg-${data.strategy_status === 'active' ? 'success' : 'secondary'}">${data.strategy_status}</span>`);

    // Update stats
    const stats = data.stats;
    updateElement('totalInvested', formatCurrency(stats.total_invested));
    updateElement('currentValue', formatCurrency(stats.current_value));
    updateElement('unrealizedPnl', formatCurrency(stats.unrealized_pnl));
    updateElement('gridProgress', `${stats.grid_filled}/${stats.total_grids} Grids Filled`);
    updateElement('dcaRounds', stats.dca_rounds);
    updateElement('avgEntryPrice', formatCurrency(stats.avg_entry_price));

    // Update grid levels table
    updateGridLevelsTable(data.grid_levels);
}

// === WEBSOCKET CONNECTION ===
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/realtime`;

    ws = new WebSocket(wsUrl);

    ws.onopen = function () {
        console.log('WebSocket connected');
        updateConnectionStatus(true);
        if (reconnectInterval) {
            clearInterval(reconnectInterval);
            reconnectInterval = null;
        }
    };

    ws.onmessage = function (event) {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };

    ws.onclose = function () {
        console.log('WebSocket disconnected');
        updateConnectionStatus(false);
        // Attempt to reconnect every 5 seconds
        if (!reconnectInterval) {
            reconnectInterval = setInterval(connectWebSocket, 5000);
        }
    };

    ws.onerror = function (error) {
        console.error('WebSocket error:', error);
        updateConnectionStatus(false);
    };
}

function handleWebSocketMessage(data) {
    // Handle real-time updates
    switch (data.type) {
        case 'bot_status':
            updateBotStatus(data);
            break;
        case 'portfolio_update':
            updatePortfolioDisplay(data);
            break;
        case 'trade_update':
            handleTradeUpdate(data);
            break;
        case 'strategy_update':
            handleStrategyUpdate(data);
            break;
        default:
            console.log('Unknown WebSocket message type:', data.type);
    }
}

function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connectionStatus');
    if (statusEl) {
        if (connected) {
            statusEl.className = 'connection-status connection-connected';
            statusEl.innerHTML = '<i class="bi bi-wifi"></i> Connected';
        } else {
            statusEl.className = 'connection-status connection-disconnected';
            statusEl.innerHTML = '<i class="bi bi-wifi-off"></i> Disconnected';
        }
    }
}

// === UTILITY FUNCTIONS ===
function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.innerHTML = value;
    }
}

function updateChangeIndicator(id, value) {
    const element = document.getElementById(id);
    if (element) {
        const isPositive = value >= 0;
        const icon = isPositive ? 'bi-arrow-up' : 'bi-arrow-down';
        const colorClass = isPositive ? 'text-success' : 'text-danger';

        element.innerHTML = `<i class="bi ${icon} ${colorClass}"></i> ${formatPercentage(Math.abs(value), true)}`;
        element.className = `metric-change ${isPositive ? 'positive' : 'negative'}`;
    }
}

function formatCurrency(amount, currency = 'USD') {
    if (typeof amount === 'undefined' || amount === null) return '$0.00';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

function formatPercentage(value, showSign = false) {
    if (typeof value === 'undefined' || value === null) return '0.00%';
    const sign = showSign && value > 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
}

function formatNumber(value, decimals = 2) {
    if (typeof value === 'undefined' || value === null) return '0';
    return value.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

// === TABLE UPDATE FUNCTIONS ===
function updateRecentTradesTable(trades) {
    const tableBody = document.querySelector('#recentTradesTable tbody');
    if (!tableBody || !trades) return;

    tableBody.innerHTML = trades.map(trade => `
        <tr>
            <td>${trade.symbol}</td>
            <td><span class="badge bg-${trade.side === 'buy' ? 'success' : 'danger'}">${trade.side.toUpperCase()}</span></td>
            <td>${formatNumber(trade.amount, 6)}</td>
            <td>${formatCurrency(trade.price)}</td>
            <td>${formatCurrency(trade.value)}</td>
            <td class="${trade.pnl >= 0 ? 'text-success' : 'text-danger'}">${formatCurrency(trade.pnl)}</td>
            <td><span class="badge bg-success">${trade.status}</span></td>
        </tr>
    `).join('');
}

function updateStrategiesTable(strategies) {
    const tableBody = document.querySelector('#strategiesTable tbody');
    if (!tableBody || !strategies) return;

    tableBody.innerHTML = strategies.map(strategy => `
        <tr>
            <td>
                <div class="d-flex align-items-center">
                    <i class="bi bi-robot text-primary me-2"></i>
                    <div>
                        <div class="fw-bold">${strategy.name}</div>
                        <small class="text-muted">${strategy.symbol}</small>
                    </div>
                </div>
            </td>
            <td><span class="badge bg-${strategy.status === 'active' ? 'success' : 'secondary'}">${strategy.status}</span></td>
            <td class="${strategy.pnl >= 0 ? 'text-success' : 'text-danger'}">${formatCurrency(strategy.pnl)}</td>
            <td>${formatPercentage(strategy.pnl_percent)}</td>
            <td>${strategy.trades}</td>
            <td>${formatPercentage(strategy.win_rate)}</td>
            <td>
                <span class="badge bg-${strategy.risk_level === 'low' ? 'success' : strategy.risk_level === 'medium' ? 'warning' : 'danger'}">
                    ${strategy.risk_level}
                </span>
            </td>
        </tr>
    `).join('');
}

function updateGridLevelsTable(gridLevels) {
    const tableBody = document.querySelector('#gridLevelsTable tbody');
    if (!tableBody || !gridLevels) return;

    tableBody.innerHTML = gridLevels.map(level => `
        <tr>
            <td>${formatCurrency(level.price)}</td>
            <td><span class="badge bg-${level.type === 'buy' ? 'success' : 'warning'}">${level.type.toUpperCase()}</span></td>
            <td>${formatNumber(level.amount, 6)}</td>
            <td><span class="badge bg-${level.status === 'filled' ? 'success' : 'secondary'}">${level.status}</span></td>
        </tr>
    `).join('');
}

// === BOT CONTROL FUNCTIONS ===
function startBot() {
    fetch('/api/bot/start', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Bot started successfully', 'success');
                loadBotStatus();
            } else {
                showNotification('Failed to start bot: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error starting bot:', error);
            showNotification('Error starting bot', 'error');
        });
}

function stopBot() {
    fetch('/api/bot/stop', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Bot stopped successfully', 'success');
                loadBotStatus();
            } else {
                showNotification('Failed to stop bot: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error stopping bot:', error);
            showNotification('Error stopping bot', 'error');
        });
}

function pauseBot() {
    fetch('/api/bot/pause', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Bot paused successfully', 'warning');
                loadBotStatus();
            } else {
                showNotification('Failed to pause bot: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error pausing bot:', error);
            showNotification('Error pausing bot', 'error');
        });
}

// === NOTIFICATION FUNCTIONS ===
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';

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
}

// === PAGE-SPECIFIC FEATURES ===
function setupPageSpecificFeatures() {
    const currentPage = getCurrentPage();

    // Setup bot control buttons
    setupBotControls();

    // Setup refresh button
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            loadAllData();
            showNotification('Data refreshed', 'success');
        });
    }

    // Page-specific setup
    switch (currentPage) {
        case 'grid-dca':
            setupGridDcaControls();
            break;
        case 'strategies':
            setupStrategyControls();
            break;
    }
}

function setupBotControls() {
    // Make bot control functions globally available
    window.confirmAction = function (action) {
        const actionMap = {
            'start': { func: startBot, message: 'Are you sure you want to start the bot?' },
            'stop': { func: stopBot, message: 'Are you sure you want to stop the bot?' },
            'pause': { func: pauseBot, message: 'Are you sure you want to pause the bot?' }
        };

        const actionConfig = actionMap[action];
        if (actionConfig) {
            if (confirm(actionConfig.message)) {
                actionConfig.func();
            }
        }
    };

    // Make refresh function globally available
    window.refreshData = function () {
        loadAllData();
        showNotification('Data refreshed', 'success');
    };
}

function setupGridDcaControls() {
    const startBtn = document.getElementById('startStrategyBtn');
    const stopBtn = document.getElementById('stopStrategyBtn');

    if (startBtn) {
        startBtn.addEventListener('click', () => {
            if (confirm('Start Grid DCA strategy?')) {
                // Implement start grid DCA
                showNotification('Grid DCA strategy started', 'success');
            }
        });
    }

    if (stopBtn) {
        stopBtn.addEventListener('click', () => {
            if (confirm('Stop Grid DCA strategy?')) {
                // Implement stop grid DCA
                showNotification('Grid DCA strategy stopped', 'warning');
            }
        });
    }
}

function setupStrategyControls() {
    // Setup strategy-specific controls
    console.log('Strategy controls setup');
}

// === MOBILE SIDEBAR ===
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('show');
    }
}

// Make toggleSidebar globally available
window.toggleSidebar = toggleSidebar;

// === CLEANUP ===
window.addEventListener('beforeunload', function () {
    if (ws) {
        ws.close();
    }
    if (dataRefreshInterval) {
        clearInterval(dataRefreshInterval);
    }
    if (reconnectInterval) {
        clearInterval(reconnectInterval);
    }
});
if (typeof updatePortfolioData === 'function' && data.portfolio) {
    updatePortfolioData(data.portfolio);
}
if (typeof updateOrdersData === 'function' && data.orders) {
    updateOrdersData(data.orders);
}
if (typeof updateStrategiesData === 'function' && data.strategies) {
    updateStrategiesData(data.strategies);
}
if (typeof updateTradesData === 'function' && data.trades) {
    updateTradesData(data.trades);
}


// === DATA REFRESH ===
function refreshData() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'request_data',
            data_type: 'all'
        }));
        showNotification('Data refreshed', 'success');
    } else {
        location.reload();
    }
}

// === BOT CONTROL ACTIONS ===
function confirmAction(action) {
    const actionMessages = {
        'start': 'start the trading bot',
        'stop': 'stop the trading bot',
        'pause': 'pause the trading bot',
        'restart': 'restart the trading bot'
    };

    const message = actionMessages[action] || `${action} the trading bot`;

    if (confirm(`Are you sure you want to ${message}?`)) {
        executeAction(action);
    }
}

function executeAction(action) {
    fetch(`/api/control/${action}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
        .then(response => {
            if (response.ok) {
                showNotification(`Bot ${action} command executed successfully`, 'success');
                // Reload page after a short delay to show notification
                setTimeout(() => location.reload(), 1500);
            } else {
                return response.json().then(data => {
                    throw new Error(data.detail || 'Unknown error occurred');
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification(`Action failed: ${error.message}`, 'error');
        });
}

// === NOTIFICATION SYSTEM ===
function showNotification(message, type = 'info', duration = 4000) {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.custom-notification');
    existingNotifications.forEach(notification => notification.remove());

    const notification = document.createElement('div');
    notification.className = `alert alert-${getBootstrapAlertClass(type)} alert-dismissible fade show position-fixed custom-notification`;
    notification.style.cssText = 'top: 80px; right: 20px; z-index: 9999; min-width: 300px; max-width: 400px;';

    notification.innerHTML = `
    <div class="d-flex align-items-center">
      <i class="bi ${getNotificationIcon(type)} me-2"></i>
      <div class="flex-grow-1">${message}</div>
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
  `;

    document.body.appendChild(notification);

    // Auto-remove after specified duration
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, duration);
}

function getBootstrapAlertClass(type) {
    const classMap = {
        'error': 'danger',
        'success': 'success',
        'warning': 'warning',
        'info': 'info'
    };
    return classMap[type] || 'info';
}

function getNotificationIcon(type) {
    const iconMap = {
        'error': 'bi-exclamation-triangle-fill',
        'success': 'bi-check-circle-fill',
        'warning': 'bi-exclamation-circle-fill',
        'info': 'bi-info-circle-fill'
    };
    return iconMap[type] || 'bi-info-circle-fill';
}

// === UTILITY FUNCTIONS ===
function formatCurrency(value, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value || 0);
}

function formatPercentage(value, showSign = true) {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
        signDisplay: showSign ? 'always' : 'auto'
    }).format((value || 0) / 100);
}

function formatNumber(value, decimals = 2) {
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value || 0);
}

function formatDateTime(dateString) {
    if (!dateString) return 'N/A';

    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    }).format(date);
}

function formatTime(dateString) {
    if (!dateString) return 'N/A';

    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    }).format(date);
}

// === MOBILE FUNCTIONALITY ===
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('show');
    }
}

// Close sidebar when clicking outside on mobile
function handleOutsideClick(event) {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.querySelector('.mobile-menu-toggle');

    if (window.innerWidth <= 768 &&
        sidebar &&
        !sidebar.contains(event.target) &&
        toggle &&
        !toggle.contains(event.target) &&
        sidebar.classList.contains('show')) {
        sidebar.classList.remove('show');
    }
}

// === LOADING STATES ===
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="loading-spinner"></div> Loading...';
    }
}

function hideLoading(elementId, content = '') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = content;
    }
}

// === FORM HELPERS ===
function serializeForm(form) {
    const formData = new FormData(form);
    const data = {};

    for (let [key, value] of formData.entries()) {
        // Handle checkboxes and multiple values
        if (data[key]) {
            if (Array.isArray(data[key])) {
                data[key].push(value);
            } else {
                data[key] = [data[key], value];
            }
        } else {
            data[key] = value;
        }
    }

    return data;
}

function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// === CHART HELPERS ===
function createChart(canvasId, config) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.error(`Canvas element with id '${canvasId}' not found`);
        return null;
    }

    return new Chart(ctx, config);
}

function updateChart(chart, newData) {
    if (chart && newData) {
        chart.data = newData;
        chart.update('active');
    }
}

// === ERROR HANDLING ===
function handleError(error, context = '') {
    console.error(`Error in ${context}:`, error);
    showNotification(`An error occurred: ${error.message}`, 'error');
}

// === LOCAL STORAGE HELPERS ===
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
        return true;
    } catch (error) {
        console.error('Failed to save to localStorage:', error);
        return false;
    }
}

function loadFromLocalStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        console.error('Failed to load from localStorage:', error);
        return defaultValue;
    }
}

// === DEBOUNCE HELPER ===
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// === INITIALIZATION ===
document.addEventListener('DOMContentLoaded', function () {
    console.log('Trading Bot Dashboard initializing...');

    // Initialize WebSocket connection
    connectWebSocket();

    // Add event listeners
    document.addEventListener('click', handleOutsideClick);

    // Initialize any saved preferences
    const savedTheme = loadFromLocalStorage('theme');
    if (savedTheme) {
        document.body.setAttribute('data-theme', savedTheme);
    }

    console.log('Trading Bot Dashboard initialized successfully');
});

// === WINDOW EVENT HANDLERS ===
window.addEventListener('beforeunload', function () {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
    }
});

window.addEventListener('resize', debounce(function () {
    // Handle window resize events
    const sidebar = document.getElementById('sidebar');
    if (window.innerWidth > 768 && sidebar && sidebar.classList.contains('show')) {
        sidebar.classList.remove('show');
    }
}, 250));

// === EXPOSE GLOBAL FUNCTIONS ===
window.TradingBot = {
    connectWebSocket,
    refreshData,
    confirmAction,
    showNotification,
    toggleSidebar,
    formatCurrency,
    formatPercentage,
    formatNumber,
    formatDateTime,
    formatTime,
    createChart,
    updateChart,
    saveToLocalStorage,
    loadFromLocalStorage
};
