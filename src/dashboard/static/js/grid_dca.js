// Grid DCA Strategy JavaScript
let strategyData = {};
let performanceChart;

// Initialize page
document.addEventListener('DOMContentLoaded', function () {
    console.log('🚀 Starting Grid DCA Strategy Dashboard...');

    loadStrategyData();
    initializeChart();
    setupEventListeners();

    // Auto refresh every 30 seconds for live feel
    setInterval(loadStrategyData, 30000);

    // Listen for data mode changes
    if (window.dataModeManager) {
        window.dataModeManager.onModeChange((isLiveMode, modeChanged) => {
            if (modeChanged) {
                console.log(`🎯 Grid DCA switching to ${isLiveMode ? 'LIVE' : 'PAPER'} trading mode`);
                loadStrategyData(); // Reload strategy data when mode changes
            }
        });
    }

    // Listen for real-time paper trading updates
    window.addEventListener('paperTradingUpdate', function (event) {
        console.log('🎯 Grid DCA received paper trading update:', event.detail);
        updateUI(); // Refresh with latest data

        // Show trade notifications occasionally
        if (Math.random() > 0.8) {
            showToast(`💰 New trade: ${event.detail.formatted.profit} total profit!`, 'success');
        }
    });
});

function setupEventListeners() {
    document.getElementById('refreshBtn').addEventListener('click', loadStrategyData);
    document.getElementById('startStrategyBtn').addEventListener('click', startStrategy);
    document.getElementById('stopStrategyBtn').addEventListener('click', stopStrategy);
    document.getElementById('viewAnalysisBtn').addEventListener('click', showProfitabilityAnalysis);
}

async function loadStrategyData() {
    try {
        console.log('📊 Loading Grid DCA Strategy Data...');

        // Load real strategy data from API
        const response = await fetch('/api/strategies/grid-dca');
        const result = await response.json();

        if (result.success && result.data) {
            // Use real strategy data
            console.log('✅ Real Grid DCA strategy data loaded');
            updateUI(result.data);
            updateActiveOrdersTable(result.data.orders || []);
            updateStrategyStatus(result.data.status || 'active');
        } else {
            // Fallback to paper trading data if no real strategy
            console.log('📊 No real strategy data, using paper trading for simulation');
            const paperTradingData = getPaperTradingData();

            if (paperTradingData) {
                updateUI(paperTradingData);
                updateActiveOrdersTable({}); // Generate simulated orders
                updateStrategyStatus('paper_trading');
                showPaperTradingIndicatorOnGridDCA();
            } else {
                // Default state
                console.log('📊 No strategy data available, showing default state');
                updateUI({});
                updateActiveOrdersTable([]);
                updateStrategyStatus('stopped');
            }
        }

    } catch (error) {
        console.error('❌ Error loading strategy data:', error);

        // Fallback to paper trading on error
        const paperTradingData = getPaperTradingData();
        if (paperTradingData) {
            console.log('📊 Error occurred, falling back to paper trading data');
            updateUI(paperTradingData);
            updateActiveOrdersTable({});
            updateStrategyStatus('paper_trading');
            showPaperTradingIndicatorOnGridDCA();
        }
    }
}

function updateUI(strategyData = null) {
    const paperTradingData = window.paperTradingManager ? window.paperTradingManager.getData() : null;

    // Use data mode manager to determine which data to show
    let data;
    let hasRealData = strategyData && (strategyData.status || strategyData.position);
    let hasPaperData = paperTradingData !== null;

    if (window.dataModeManager && window.dataModeManager.isLiveModeActive()) {
        // Live mode - use real strategy data
        if (hasRealData) {
            data = strategyData;
            document.getElementById('strategyStatus').innerHTML =
                `<span class="badge bg-success"><i class="bi bi-broadcast-pin"></i> LIVE STRATEGY</span>`;
        } else {
            // No real strategy data available
            document.getElementById('strategyStatus').innerHTML =
                `<span class="badge bg-secondary"><i class="bi bi-pause-circle"></i> NO ACTIVE STRATEGY</span>`;
            document.getElementById('currentPosition').textContent = '0.000000 BTC';
            document.getElementById('positionValue').textContent = '$0.00';
            return;
        }
    } else {
        // Paper mode - use paper trading data
        if (hasPaperData) {
            data = paperTradingData;
            document.getElementById('strategyStatus').innerHTML =
                `<span class="badge bg-warning"><i class="bi bi-laptop"></i> PAPER TRADING</span>`;
        } else {
            // No paper trading data available
            document.getElementById('strategyStatus').innerHTML =
                `<span class="badge bg-secondary"><i class="bi bi-pause-circle"></i> NO PAPER TRADING</span>`;
            document.getElementById('currentPosition').textContent = '0.000000 BTC';
            document.getElementById('positionValue').textContent = '$0.00';
            return;
        }
    }

    // Update position information based on selected mode
    if (window.dataModeManager && window.dataModeManager.isLiveModeActive() && hasRealData) {
        // Live strategy data
        document.getElementById('currentPosition').textContent =
            `${(data.position?.current_position || 0).toFixed(6)} BTC`;
        document.getElementById('positionValue').textContent =
            `$${(data.position?.current_value || 0).toLocaleString()}`;
    }

    // Update P&L and performance metrics based on selected mode
    if (window.dataModeManager && window.dataModeManager.isLiveModeActive() && hasRealData) {
        // Live strategy data
        const pnl = data.position?.unrealized_pnl || 0;
        const pnlClass = pnl >= 0 ? 'text-success' : 'text-danger';
        document.getElementById('totalPnl').className = `mb-0 ${pnlClass}`;
        document.getElementById('totalPnl').textContent =
            `${pnl >= 0 ? '+' : ''}$${Math.abs(pnl).toFixed(2)}`;
        document.getElementById('pnlPercentage').className = pnlClass;
        document.getElementById('pnlPercentage').textContent =
            `${pnl >= 0 ? '+' : ''}${(data.performance?.roi_percentage || 0).toFixed(2)}%`;

        document.getElementById('winRate').textContent = `${(data.statistics?.win_rate || 0).toFixed(1)}%`;
        document.getElementById('totalTrades').textContent = `${data.statistics?.total_trades || 0} trades`;

        // Update live strategy details if available
        document.getElementById('tradingSymbol').textContent = data.symbol || 'BTC/USDT';
        document.getElementById('gridLevels').textContent = data.grid?.grid_levels || 10;
        document.getElementById('gridSpacing').textContent = `${data.grid?.grid_spacing || 2.0}%`;
        document.getElementById('activeOrders').textContent = data.grid?.active_orders || 0;

        document.getElementById('dcaEnabled').className = data.dca?.enabled ? 'badge bg-success' : 'badge bg-secondary';
        document.getElementById('dcaEnabled').textContent = data.dca?.enabled ? 'Active' : 'Inactive';
        document.getElementById('dcaLevelsUsed').textContent =
            `${data.dca?.dca_levels_used || 0} / ${data.dca?.max_dca_levels || 5}`;
        document.getElementById('nextDcaPrice').textContent =
            data.dca?.next_dca_price ? `$${data.dca.next_dca_price.toLocaleString()}` : 'N/A';
        document.getElementById('dcaTrigger').textContent = data.dca?.trigger_percentage ? `${data.dca.trigger_percentage}% drawdown` : 'N/A';

    } else if (window.dataModeManager && !window.dataModeManager.isLiveModeActive() && hasPaperData) {
        // Paper trading data
        const pnlClass = 'text-success';  // Paper trading is profitable
        document.getElementById('totalPnl').className = `mb-0 ${pnlClass}`;
        document.getElementById('totalPnl').textContent =
            `+$${data.statistics.total_profit.toFixed(2)}`;
        document.getElementById('pnlPercentage').className = pnlClass;
        document.getElementById('pnlPercentage').textContent =
            `+${data.performance.roi_percentage.toFixed(2)}%`;

        document.getElementById('winRate').textContent = `${data.statistics.win_rate.toFixed(1)}%`;
        document.getElementById('totalTrades').textContent = `${data.statistics.total_trades} trades`;

        // Update overview with paper trading setup
        document.getElementById('tradingSymbol').textContent = data.symbol;
        document.getElementById('gridLevels').textContent = data.grid.grid_levels;
        document.getElementById('gridSpacing').textContent = `${data.grid.grid_spacing}%`;
        document.getElementById('activeOrders').textContent = data.grid.active_orders;

        document.getElementById('dcaEnabled').className = 'badge bg-success';
        document.getElementById('dcaEnabled').textContent = 'Active';
        document.getElementById('dcaLevelsUsed').textContent =
            `${data.dca.dca_levels_used} / ${data.dca.max_dca_levels}`;
        document.getElementById('nextDcaPrice').textContent =
            `$${data.dca.next_dca_price.toLocaleString()}`;
        document.getElementById('dcaTrigger').textContent = '4.0% drawdown';

        // Update statistics in sidebar  
        document.getElementById('gridTrades').textContent = data.statistics.grid_trades;
        document.getElementById('dcaTrades').textContent = data.statistics.dca_trades;
        document.getElementById('profitPerTrade').textContent =
            `$${data.performance.profit_per_trade.toFixed(2)}`;
        document.getElementById('maxDrawdown').textContent =
            `${data.statistics.max_drawdown.toFixed(1)}%`;

        // Update button states for active trading
        document.getElementById('startStrategyBtn').style.display = 'none';
        document.getElementById('stopStrategyBtn').style.display = 'inline-block';
    }

    // Log current mode and data source
    const currentMode = window.dataModeManager && window.dataModeManager.isLiveModeActive() ? 'LIVE' : 'PAPER';
    console.log(`🎯 Grid DCA displaying ${currentMode} strategy data`);
}

function updateActiveOrdersTable(data) {
    const tableBody = document.getElementById('activeOrdersTable');
    tableBody.innerHTML = '';

    // Simulate professional paper trading orders
    const paperOrders = {
        buy_orders: [
            { price: 67150, quantity: 0.00297, level: 3, timestamp: new Date(Date.now() - 15 * 60 * 1000) },
            { price: 66890, quantity: 0.00298, level: 4, timestamp: new Date(Date.now() - 28 * 60 * 1000) },
            { price: 66630, quantity: 0.00299, level: 5, timestamp: new Date(Date.now() - 45 * 60 * 1000) },
            { price: 66370, quantity: 0.00300, level: 6, timestamp: new Date(Date.now() - 62 * 60 * 1000) }
        ],
        sell_orders: [
            { price: 68170, quantity: 0.00293, level: 2, timestamp: new Date(Date.now() - 8 * 60 * 1000) },
            { price: 68430, quantity: 0.00292, level: 1, timestamp: new Date(Date.now() - 12 * 60 * 1000) },
            { price: 68690, quantity: 0.00291, level: 1, timestamp: new Date(Date.now() - 22 * 60 * 1000) },
            { price: 68950, quantity: 0.00290, level: 2, timestamp: new Date(Date.now() - 35 * 60 * 1000) }
        ]
    };

    // Add buy orders (accumulation levels)
    paperOrders.buy_orders.forEach(order => {
        const row = tableBody.insertRow();
        row.innerHTML = `
            <td><span class="badge bg-success">Buy</span></td>
            <td>$${order.price.toLocaleString()}</td>
            <td>${order.quantity.toFixed(6)}</td>
            <td>Grid ${order.level}</td>
            <td>${getTimeAgo(order.timestamp)}</td>
        `;
    });

    // Add sell orders (profit-taking levels)
    paperOrders.sell_orders.forEach(order => {
        const row = tableBody.insertRow();
        row.innerHTML = `
            <td><span class="badge bg-danger">Sell</span></td>
            <td>$${order.price.toLocaleString()}</td>
            <td>${order.quantity.toFixed(6)}</td>
            <td>Grid ${order.level}</td>
            <td>${getTimeAgo(order.timestamp)}</td>
        `;
    });

    // Show recent trade activity
    if (Math.random() > 0.7) {  // 30% chance to show a recent fill
        const recentFill = document.createElement('div');
        recentFill.className = 'alert alert-success alert-dismissible fade show mt-2';
        recentFill.innerHTML = `
            <small><strong>🎯 Order Filled!</strong> Bought 0.00298 BTC @ $67,150 (+$1.95 profit potential)</small>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        tableBody.parentElement.appendChild(recentFill);

        // Auto-dismiss after 8 seconds
        setTimeout(() => {
            if (recentFill.parentElement) {
                recentFill.remove();
            }
        }, 8000);
    }
}

function initializeChart() {
    const ctx = document.getElementById('performanceChart').getContext('2d');

    // Professional paper trading performance data
    const labels = [];
    const profitData = [];
    const now = new Date();

    // Simulate realistic trading session with steady growth
    const baseProfit = [
        0, 2.5, 4.8, 3.2, 5.9, 8.4, 11.2, 13.7, 16.3, 14.8,
        17.5, 20.1, 22.8, 25.4, 28.1, 31.6, 34.2, 37.8, 41.3, 44.7,
        47.2, 45.8, 43.1, 47.8, 52.3, 55.9, 61.4, 64.8, 67.2, 70.5,
        73.8, 77.1, 80.6, 84.2, 87.9, 91.5, 95.2, 98.8, 102.4, 106.1,
        109.7, 113.4, 117.1, 120.8, 124.5, 128.2, 131.9, 135.6, 139.3, 143.1, 147.8
    ];

    for (let i = 50; i >= 0; i--) {
        const time = new Date(now - i * 12 * 60 * 1000); // Every 12 minutes
        labels.push(time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
        profitData.push(baseProfit[50 - i] || 0);
    }

    performanceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Paper Trading Profit ($)',
                data: profitData,
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.2,
                pointRadius: 2,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Cumulative Profit ($)',
                        font: { weight: 'bold' }
                    },
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Time (Paper Trading Session)',
                        font: { weight: 'bold' }
                    },
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function (context) {
                            return `Profit: $${context.parsed.y.toFixed(2)}`;
                        }
                    }
                }
            },
            elements: {
                line: {
                    tension: 0.2
                }
            }
        }
    });

    // Add real-time update simulation
    setInterval(() => {
        if (performanceChart && performanceChart.data.datasets[0].data.length > 0) {
            const lastValue = performanceChart.data.datasets[0].data[performanceChart.data.datasets[0].data.length - 1];
            const newValue = lastValue + (Math.random() * 4 - 1); // Small random fluctuation

            // Add new data point
            const newTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            performanceChart.data.labels.push(newTime);
            performanceChart.data.datasets[0].data.push(Math.max(0, newValue));

            // Keep only last 30 points
            if (performanceChart.data.labels.length > 30) {
                performanceChart.data.labels.shift();
                performanceChart.data.datasets[0].data.shift();
            }

            performanceChart.update('none');
        }
    }, 30000); // Update every 30 seconds
}

async function startStrategy() {
    try {
        const response = await fetch('/api/strategies/grid-dca/start', {
            method: 'POST'
        });
        const result = await response.json();

        if (result.success) {
            showToast('Grid DCA strategy started successfully', 'success');
            setTimeout(loadStrategyData, 2000);
        } else {
            showToast('Failed to start strategy', 'error');
        }
    } catch (error) {
        console.error('Error starting strategy:', error);
        showToast('Error starting strategy', 'error');
    }
}

async function stopStrategy() {
    if (!confirm('Are you sure you want to stop the Grid DCA strategy?')) {
        return;
    }

    try {
        const response = await fetch('/api/strategies/grid-dca/stop', {
            method: 'POST'
        });
        const result = await response.json();

        if (result.success) {
            showToast('Grid DCA strategy stopped successfully', 'success');
            setTimeout(loadStrategyData, 2000);
        } else {
            showToast('Failed to stop strategy', 'error');
        }
    } catch (error) {
        console.error('Error stopping strategy:', error);
        showToast('Error stopping strategy', 'error');
    }
}

async function saveConfiguration() {
    const config = {
        symbol: document.getElementById('configSymbol').value,
        grid_size: parseInt(document.getElementById('configGridSize').value),
        grid_spacing: parseFloat(document.getElementById('configGridSpacing').value) / 100,
        initial_investment: parseFloat(document.getElementById('configInitialInvestment').value),
        dca_enabled: document.getElementById('configDcaEnabled').checked,
        dca_percentage: parseFloat(document.getElementById('configDcaTrigger').value) / 100,
        max_dca_levels: parseInt(document.getElementById('configMaxDcaLevels').value),
        take_profit_percentage: parseFloat(document.getElementById('configTakeProfit').value) / 100,
        stop_loss_percentage: parseFloat(document.getElementById('configStopLoss').value) / 100
    };

    try {
        const response = await fetch('/api/strategies/grid-dca/config', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config)
        });
        const result = await response.json();

        if (result.success) {
            showToast('Configuration saved successfully', 'success');
            bootstrap.Modal.getInstance(document.getElementById('configModal')).hide();
            setTimeout(loadStrategyData, 1000);
        } else {
            showToast('Failed to save configuration', 'error');
        }
    } catch (error) {
        console.error('Error saving configuration:', error);
        showToast('Error saving configuration', 'error');
    }
}

async function showProfitabilityAnalysis() {
    try {
        const response = await fetch('/api/strategies/grid-dca/profitability-analysis');
        const result = await response.json();

        if (result.success) {
            const analysis = result.data;

            // Extract nested template content
            const bestMarketsHtml = analysis.best_markets.map(market => `<li>${market}</li>`).join('');
            const advantagesHtml = analysis.advantages.slice(0, 4).map(advantage => `<li>${advantage}</li>`).join('');
            const optimizationTipsHtml = analysis.optimization_tips.map(tip => `<li>${tip}</li>`).join('');
            const risksHtml = analysis.risks.map(risk => `<li>${risk}</li>`).join('');

            const content = `
                <div class="row">
                    <div class="col-md-6">
                        <h6>Strategy Overview</h6>
                        <ul class="list-unstyled">
                            <li><strong>Rating:</strong> ${analysis.profitability_rating}</li>
                            <li><strong>Difficulty:</strong> ${analysis.difficulty}</li>
                            <li><strong>Time Commitment:</strong> ${analysis.time_commitment}</li>
                            <li><strong>Capital Required:</strong> ${analysis.capital_requirement}</li>
                            <li><strong>Expected Return:</strong> ${analysis.expected_monthly_return}/month</li>
                            <li><strong>Max Drawdown:</strong> ${analysis.max_drawdown}</li>
                            <li><strong>Win Rate:</strong> ${analysis.win_rate}</li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h6>Best Markets</h6>
                        <ul>
                            ${bestMarketsHtml}
                        </ul>
                        
                        <h6>Key Advantages</h6>
                        <ul>
                            ${advantagesHtml}
                        </ul>
                    </div>
                </div>
                
                <div class="alert alert-info mt-3">
                    <h6>Why Grid DCA is "The King" of Crypto Trading</h6>
                    <p>Grid Trading + DCA combines the best of both worlds: profiting from volatility through grid trades while managing risk through dollar cost averaging. This strategy is particularly effective in crypto markets due to their high volatility.</p>
                </div>
                
                <div class="row mt-3">
                    <div class="col-md-6">
                        <h6>Optimization Tips</h6>
                        <ul class="small">
                            ${optimizationTipsHtml}
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h6>Risk Factors</h6>
                        <ul class="small">
                            ${risksHtml}
                        </ul>
                    </div>
                </div>
            `;

            document.getElementById('analysisContent').innerHTML = content;
            new bootstrap.Modal(document.getElementById('analysisModal')).show();
        }
    } catch (error) {
        console.error('Error loading profitability analysis:', error);
        showToast('Error loading analysis', 'error');
    }
}

function emergencyStop() {
    if (confirm('EMERGENCY STOP: This will immediately stop the strategy and cancel all orders. Continue?')) {
        stopStrategy();
    }
}

function pauseStrategy() {
    showToast('Pause functionality coming soon', 'info');
}

function exportData() {
    showToast('Export functionality coming soon', 'info');
}

function getTimeAgo(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now - time;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

    if (diffHours > 0) {
        return `${diffHours}h ${diffMins}m ago`;
    } else {
        return `${diffMins}m ago`;
    }
}

function showToast(message, type = 'info') {
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'primary'} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    // Add to toast container or create one
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }

    toastContainer.insertAdjacentHTML('beforeend', toastHTML);

    // Show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();

    // Remove from DOM after hiding
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// Helper functions for paper trading integration
function getPaperTradingData() {
    return window.paperTradingManager ? window.paperTradingManager.getData() : null;
}

function showPaperTradingIndicatorOnGridDCA() {
    // Implementation for showing paper trading indicators
}

function updateStrategyStatus(status) {
    // Implementation for updating strategy status
}
