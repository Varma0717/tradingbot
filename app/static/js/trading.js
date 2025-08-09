// Trading interface JavaScript
class TradingInterface {
    constructor() {
        this.initializeEventListeners();
        this.updateCharts();
    }

    initializeEventListeners() {
        // Order form submission
        const orderForm = document.getElementById('orderForm');
        if (orderForm) {
            orderForm.addEventListener('submit', this.handleOrderSubmission.bind(this));
        }

        // Strategy toggle switches
        const strategyToggles = document.querySelectorAll('.strategy-toggle');
        strategyToggles.forEach(toggle => {
            toggle.addEventListener('change', this.handleStrategyToggle.bind(this));
        });

        // Real-time updates toggle
        const realtimeToggle = document.getElementById('realtimeUpdates');
        if (realtimeToggle) {
            realtimeToggle.addEventListener('change', this.toggleRealtimeUpdates.bind(this));
        }
    }

    handleOrderSubmission(event) {
        event.preventDefault();

        const formData = new FormData(event.target);
        const orderData = {
            symbol: formData.get('symbol'),
            quantity: formData.get('quantity'),
            order_type: formData.get('order_type'),
            side: formData.get('side'),
            trade_mode: formData.get('trade_mode'),
            price: formData.get('price')
        };

        // Validate order
        if (!this.validateOrder(orderData)) {
            return;
        }

        // Show loading state
        this.showOrderLoading();

        // Submit order
        fetch('/user/trade', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams(orderData)
        })
            .then(response => response.json())
            .then(data => {
                this.handleOrderResponse(data);
            })
            .catch(error => {
                console.error('Order submission error:', error);
                this.showAlert('Order submission failed', 'error');
            })
            .finally(() => {
                this.hideOrderLoading();
            });
    }

    validateOrder(orderData) {
        if (!orderData.symbol || !orderData.quantity || !orderData.side) {
            this.showAlert('Please fill all required fields', 'error');
            return false;
        }

        if (orderData.order_type === 'limit' && !orderData.price) {
            this.showAlert('Price is required for limit orders', 'error');
            return false;
        }

        if (parseInt(orderData.quantity) <= 0) {
            this.showAlert('Quantity must be greater than 0', 'error');
            return false;
        }

        return true;
    }

    handleStrategyToggle(event) {
        const strategyId = event.target.dataset.strategyId;
        const isActive = event.target.checked;

        fetch(`/user/strategy/${strategyId}/toggle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ active: isActive })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showAlert(`Strategy ${isActive ? 'activated' : 'deactivated'}`, 'success');
                } else {
                    event.target.checked = !isActive; // Revert toggle
                    this.showAlert(data.message || 'Failed to update strategy', 'error');
                }
            })
            .catch(error => {
                console.error('Strategy toggle error:', error);
                event.target.checked = !isActive; // Revert toggle
                this.showAlert('Failed to update strategy', 'error');
            });
    }

    toggleRealtimeUpdates(event) {
        if (event.target.checked) {
            this.startRealtimeUpdates();
        } else {
            this.stopRealtimeUpdates();
        }
    }

    startRealtimeUpdates() {
        this.realtimeInterval = setInterval(() => {
            this.updateDashboardData();
        }, 5000); // Update every 5 seconds
    }

    stopRealtimeUpdates() {
        if (this.realtimeInterval) {
            clearInterval(this.realtimeInterval);
        }
    }

    updateDashboardData() {
        fetch('/api/dashboard/data')
            .then(response => response.json())
            .then(data => {
                this.updatePnLDisplay(data.pnl);
                this.updatePositions(data.positions);
                this.updateRecentTrades(data.recent_trades);
            })
            .catch(error => {
                console.error('Dashboard update error:', error);
            });
    }

    updateCharts() {
        // Initialize or update trading charts
        this.initializePnLChart();
        this.initializePortfolioChart();
    }

    initializePnLChart() {
        const ctx = document.getElementById('pnlChart');
        if (!ctx) return;

        this.pnlChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [], // Will be populated with dates
                datasets: [{
                    label: 'P&L',
                    data: [],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
    }

    initializePortfolioChart() {
        const ctx = document.getElementById('portfolioChart');
        if (!ctx) return;

        this.portfolioChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#EF4444',
                        '#10B981',
                        '#3B82F6',
                        '#F59E0B',
                        '#8B5CF6'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    showOrderLoading() {
        const submitBtn = document.getElementById('orderSubmitBtn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loader"></span> Placing Order...';
        }
    }

    hideOrderLoading() {
        const submitBtn = document.getElementById('orderSubmitBtn');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Place Order';
        }
    }

    handleOrderResponse(data) {
        if (data.success) {
            this.showAlert('Order placed successfully!', 'success');
            this.clearOrderForm();
            this.updateDashboardData();
        } else {
            this.showAlert(data.message || 'Order failed', 'error');
        }
    }

    clearOrderForm() {
        const form = document.getElementById('orderForm');
        if (form) {
            form.reset();
        }
    }

    updatePnLDisplay(pnlData) {
        const elements = {
            daily: document.getElementById('dailyPnL'),
            monthly: document.getElementById('monthlyPnL'),
            total: document.getElementById('totalPnL')
        };

        Object.keys(elements).forEach(key => {
            if (elements[key] && pnlData[key] !== undefined) {
                elements[key].textContent = `₹${pnlData[key].toLocaleString()}`;
                elements[key].className = pnlData[key] >= 0 ? 'text-green-600' : 'text-red-600';
            }
        });
    }

    updatePositions(positions) {
        const container = document.getElementById('positionsContainer');
        if (!container) return;

        container.innerHTML = positions.map(position => `
            <div class="bg-white p-4 rounded-lg shadow">
                <div class="flex justify-between items-center">
                    <span class="font-medium">${position.symbol}</span>
                    <span class="text-sm ${position.pnl >= 0 ? 'text-green-600' : 'text-red-600'}">
                        ₹${position.pnl.toLocaleString()}
                    </span>
                </div>
                <div class="text-sm text-gray-600">
                    Qty: ${position.quantity} | Avg: ₹${position.avg_price}
                </div>
            </div>
        `).join('');
    }

    updateRecentTrades(trades) {
        const container = document.getElementById('recentTradesContainer');
        if (!container) return;

        container.innerHTML = trades.map(trade => `
            <div class="bg-white p-3 rounded-lg shadow">
                <div class="flex justify-between">
                    <span class="font-medium">${trade.symbol}</span>
                    <span class="text-sm ${trade.side === 'buy' ? 'text-green-600' : 'text-red-600'}">
                        ${trade.side.toUpperCase()}
                    </span>
                </div>
                <div class="text-sm text-gray-600">
                    ${trade.quantity} @ ₹${trade.price}
                </div>
            </div>
        `).join('');
    }

    showAlert(message, type = 'info') {
        // Create alert element
        const alert = document.createElement('div');
        alert.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${type === 'success' ? 'bg-green-500 text-white' :
                type === 'error' ? 'bg-red-500 text-white' :
                    type === 'warning' ? 'bg-yellow-500 text-white' :
                        'bg-blue-500 text-white'
            }`;
        alert.textContent = message;

        document.body.appendChild(alert);

        // Auto remove after 3 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 3000);
    }
}

// Initialize trading interface when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    new TradingInterface();
});

// Add CSS for loader
const style = document.createElement('style');
style.textContent = `
    .loader {
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid #ffffff;
        border-radius: 50%;
        border-top-color: transparent;
        animation: spin 1s ease-in-out infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);
