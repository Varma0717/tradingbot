/**
 * Trading Bot Dashboard - Main JavaScript File
 * Handles WebSocket connections, UI interactions, and utility functions
 */

// === GLOBAL VARIABLES ===
let ws = null;
let reconnectInterval = null;

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

function handleWebSocketMessage(data) {
    // Handle different message types
    switch (data.type) {
        case 'initial_data':
        case 'periodic_update':
            updateDashboardData(data.data);
            break;
        case 'broadcast_update':
            updateDashboardData(data.data);
            break;
        case 'error':
            console.error('WebSocket error:', data.message);
            showNotification('WebSocket error: ' + data.message, 'error');
            break;
        default:
            console.log('Unknown message type:', data.type);
    }
}

function updateDashboardData(data) {
    // Update dashboard elements with real-time data
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
