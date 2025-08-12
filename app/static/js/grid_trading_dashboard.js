/* 
Pionex-style Grid Trading Dashboard Enhancements
Advanced UI for grid trading monitoring and control
*/

// Grid Trading Dashboard Class
class GridTradingDashboard {
    constructor() {
        this.gridStatusInterval = null;
        this.performanceInterval = null;
        this.isGridActive = false;
        this.chartInstance = null;

        this.init();
    }

    init() {
        this.createGridDashboard();
        this.bindGridEvents();
        this.checkGridStatus();

        // Auto-refresh every 30 seconds
        this.startAutoRefresh();

        console.log('🔥 Pionex-style Grid Trading Dashboard Initialized');
    }

    createGridDashboard() {
        // Find or create grid container
        let gridContainer = document.getElementById('grid-trading-panel');

        if (!gridContainer) {
            // Create new grid panel
            gridContainer = document.createElement('div');
            gridContainer.id = 'grid-trading-panel';
            gridContainer.className = 'dashboard-panel grid-trading-panel';

            // Add to main dashboard
            const dashboardContainer = document.querySelector('.dashboard-container') || document.body;
            dashboardContainer.appendChild(gridContainer);
        }

        gridContainer.innerHTML = `
            <div class="panel-header">
                <h2>🔥 Pionex-Style Grid Trading</h2>
                <div class="grid-controls">
                    <button id="start-grid-btn" class="btn btn-success">
                        <i class="fas fa-play"></i> Start Grid Bot
                    </button>
                    <button id="stop-grid-btn" class="btn btn-danger" style="display: none;">
                        <i class="fas fa-stop"></i> Stop Grid Bot
                    </button>
                    <button id="grid-config-btn" class="btn btn-secondary">
                        <i class="fas fa-cog"></i> Configure
                    </button>
                </div>
            </div>
            
            <div class="grid-status-overview">
                <div class="status-cards">
                    <div class="status-card profit-card">
                        <div class="card-icon">💰</div>
                        <div class="card-content">
                            <h3 id="total-profit">$0.00</h3>
                            <p>Total Profit</p>
                        </div>
                    </div>
                    
                    <div class="status-card roi-card">
                        <div class="card-icon">📈</div>
                        <div class="card-content">
                            <h3 id="daily-roi">0.00%</h3>
                            <p>Daily ROI</p>
                        </div>
                    </div>
                    
                    <div class="status-card grids-card">
                        <div class="card-icon">🔥</div>
                        <div class="card-content">
                            <h3 id="active-grids">0</h3>
                            <p>Active Grids</p>
                        </div>
                    </div>
                    
                    <div class="status-card cycles-card">
                        <div class="card-icon">🔄</div>
                        <div class="card-content">
                            <h3 id="total-cycles">0</h3>
                            <p>Completed Cycles</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="grid-performance-section">
                <div class="performance-header">
                    <h3>📊 Grid Performance</h3>
                    <div class="target-progress">
                        <span>Daily Target Progress:</span>
                        <div class="progress-bar">
                            <div id="target-progress-fill" class="progress-fill"></div>
                        </div>
                        <span id="target-percentage">0%</span>
                    </div>
                </div>
                
                <div class="grid-details">
                    <div class="grid-table-container">
                        <table class="grid-table">
                            <thead>
                                <tr>
                                    <th>Symbol</th>
                                    <th>Status</th>
                                    <th>Investment</th>
                                    <th>Profit</th>
                                    <th>ROI</th>
                                    <th>Cycles</th>
                                </tr>
                            </thead>
                            <tbody id="grid-table-body">
                                <!-- Grid details will be populated here -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="grid-log-section">
                <div class="log-header">
                    <h3>📝 Trading Log</h3>
                    <button id="clear-log-btn" class="btn btn-sm">Clear Log</button>
                </div>
                <div id="grid-trading-log" class="trading-log">
                    <div class="log-entry">
                        <span class="log-time">${new Date().toLocaleTimeString()}</span>
                        <span class="log-message">Grid Trading Dashboard Ready</span>
                    </div>
                </div>
            </div>
            
            <!-- Grid Configuration Modal -->
            <div id="grid-config-modal" class="modal" style="display: none;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>⚙️ Grid Trading Configuration</h3>
                        <button class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="config-section">
                            <label>Initial Capital ($)</label>
                            <input type="number" id="config-capital" value="10000" min="1000" step="1000">
                        </div>
                        
                        <div class="config-section">
                            <label>Trading Symbols</label>
                            <div class="symbol-selector">
                                <label><input type="checkbox" value="AAPL" checked> AAPL</label>
                                <label><input type="checkbox" value="TSLA" checked> TSLA</label>
                                <label><input type="checkbox" value="MSFT" checked> MSFT</label>
                                <label><input type="checkbox" value="NVDA" checked> NVDA</label>
                                <label><input type="checkbox" value="AMZN" checked> AMZN</label>
                                <label><input type="checkbox" value="GOOGL" checked> GOOGL</label>
                            </div>
                        </div>
                        
                        <div class="config-section">
                            <label>Target Daily Return (%)</label>
                            <input type="number" id="config-daily-target" value="3" min="1" max="10" step="0.5">
                        </div>
                        
                        <div class="config-section">
                            <label>Grid Count per Symbol</label>
                            <input type="number" id="config-grid-count" value="20" min="10" max="50" step="5">
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button id="save-config-btn" class="btn btn-primary">Save Configuration</button>
                        <button id="cancel-config-btn" class="btn btn-secondary">Cancel</button>
                    </div>
                </div>
            </div>
        `;
    }

    bindGridEvents() {
        // Start/Stop buttons
        document.getElementById('start-grid-btn')?.addEventListener('click', () => this.startGridTrading());
        document.getElementById('stop-grid-btn')?.addEventListener('click', () => this.stopGridTrading());

        // Configuration
        document.getElementById('grid-config-btn')?.addEventListener('click', () => this.showConfigModal());
        document.getElementById('save-config-btn')?.addEventListener('click', () => this.saveConfiguration());
        document.getElementById('cancel-config-btn')?.addEventListener('click', () => this.hideConfigModal());

        // Modal close
        document.querySelector('#grid-config-modal .modal-close')?.addEventListener('click', () => this.hideConfigModal());

        // Clear log
        document.getElementById('clear-log-btn')?.addEventListener('click', () => this.clearTradingLog());
    }

    async startGridTrading() {
        try {
            const startBtn = document.getElementById('start-grid-btn');
            const stopBtn = document.getElementById('stop-grid-btn');

            startBtn.disabled = true;
            startBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';

            const response = await fetch('/api/grid/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (result.status === 'success') {
                this.isGridActive = true;
                startBtn.style.display = 'none';
                stopBtn.style.display = 'inline-block';

                this.addLogEntry('🚀 Grid Trading Started Successfully!', 'success');
                this.addLogEntry(`💼 Capital: $${result.config.initial_capital.toLocaleString()}`, 'info');
                this.addLogEntry(`🎯 Target: ${result.expected_daily_return} daily return`, 'info');

                // Show success notification
                this.showNotification('Grid Trading Started!', 'Grid bots are now active and hunting for profits', 'success');

            } else {
                throw new Error(result.message || 'Failed to start grid trading');
            }

        } catch (error) {
            console.error('Grid start error:', error);
            this.addLogEntry(`❌ Failed to start: ${error.message}`, 'error');
            this.showNotification('Start Failed', error.message, 'error');

            // Reset button
            const startBtn = document.getElementById('start-grid-btn');
            startBtn.disabled = false;
            startBtn.innerHTML = '<i class="fas fa-play"></i> Start Grid Bot';
        }
    }

    async stopGridTrading() {
        try {
            const response = await fetch('/api/grid/stop', {
                method: 'POST'
            });

            const result = await response.json();

            if (result.status === 'success') {
                this.isGridActive = false;

                document.getElementById('start-grid-btn').style.display = 'inline-block';
                document.getElementById('stop-grid-btn').style.display = 'none';

                this.addLogEntry('🛑 Grid Trading Stopped', 'warning');
                this.showNotification('Grid Trading Stopped', 'All grid bots have been deactivated', 'warning');

            } else {
                throw new Error(result.message || 'Failed to stop grid trading');
            }

        } catch (error) {
            console.error('Grid stop error:', error);
            this.addLogEntry(`❌ Failed to stop: ${error.message}`, 'error');
        }
    }

    async checkGridStatus() {
        try {
            const response = await fetch('/api/grid/status');
            const result = await response.json();

            if (result.status === 'success') {
                this.updateGridDisplay(result.data);
            }

        } catch (error) {
            console.error('Grid status check error:', error);
        }
    }

    updateGridDisplay(statusData) {
        // Update status cards
        document.getElementById('total-profit').textContent = `$${statusData.total_profit?.toFixed(2) || '0.00'}`;
        document.getElementById('daily-roi').textContent = `${statusData.daily_roi?.toFixed(2) || '0.00'}%`;
        document.getElementById('active-grids').textContent = statusData.active_grids || '0';
        document.getElementById('total-cycles').textContent = statusData.total_cycles || '0';

        // Update target progress
        const targetProgress = Math.min(100, (statusData.daily_roi || 0) / 3 * 100); // 3% target
        document.getElementById('target-progress-fill').style.width = `${targetProgress}%`;
        document.getElementById('target-percentage').textContent = `${targetProgress.toFixed(1)}%`;

        // Update grid table
        this.updateGridTable(statusData.grid_details || {});

        // Update panel status indicator
        const panel = document.getElementById('grid-trading-panel');
        if (statusData.status === 'running') {
            panel.classList.add('active');
            this.isGridActive = true;

            document.getElementById('start-grid-btn').style.display = 'none';
            document.getElementById('stop-grid-btn').style.display = 'inline-block';
        } else {
            panel.classList.remove('active');
            this.isGridActive = false;

            document.getElementById('start-grid-btn').style.display = 'inline-block';
            document.getElementById('stop-grid-btn').style.display = 'none';
        }
    }

    updateGridTable(gridDetails) {
        const tableBody = document.getElementById('grid-table-body');

        if (!gridDetails || Object.keys(gridDetails).length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="no-data">No active grids</td></tr>';
            return;
        }

        const rows = Object.entries(gridDetails).map(([symbol, data]) => {
            const statusClass = data.cycles > 0 ? 'status-active' : 'status-init';
            const statusText = data.cycles > 0 ? 'Active' : 'Initializing';
            const profitClass = data.profit > 0 ? 'profit-positive' : 'profit-neutral';
            const roiClass = data.roi > 0 ? 'roi-positive' : 'roi-neutral';

            return `
                <tr>
                    <td class="symbol-cell">
                        <span class="symbol-badge">${symbol}</span>
                    </td>
                    <td class="status-cell">
                        <span class="status-badge ${statusClass}">${statusText}</span>
                    </td>
                    <td class="investment-cell">$${data.investment?.toFixed(2) || '0.00'}</td>
                    <td class="profit-cell ${profitClass}">
                        $${data.profit?.toFixed(2) || '0.00'}
                    </td>
                    <td class="roi-cell ${roiClass}">
                        ${data.roi?.toFixed(2) || '0.00'}%
                    </td>
                    <td class="cycles-cell">${data.cycles || 0}</td>
                </tr>
            `;
        }).join('');

        tableBody.innerHTML = rows;
    }

    showConfigModal() {
        document.getElementById('grid-config-modal').style.display = 'flex';
    }

    hideConfigModal() {
        document.getElementById('grid-config-modal').style.display = 'none';
    }

    async saveConfiguration() {
        try {
            const capital = parseFloat(document.getElementById('config-capital').value);
            const dailyTarget = parseFloat(document.getElementById('config-daily-target').value) / 100;
            const gridCount = parseInt(document.getElementById('config-grid-count').value);

            // Get selected symbols
            const symbols = Array.from(document.querySelectorAll('.symbol-selector input:checked'))
                .map(input => input.value);

            const config = {
                initial_capital: capital,
                target_daily_return: dailyTarget,
                grid_count_per_symbol: gridCount,
                symbols: symbols
            };

            const response = await fetch('/api/grid/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            const result = await response.json();

            if (result.status === 'success') {
                this.hideConfigModal();
                this.showNotification('Configuration Saved', 'Grid trading settings updated successfully', 'success');
                this.addLogEntry('⚙️ Configuration updated', 'info');
            } else {
                throw new Error(result.message);
            }

        } catch (error) {
            console.error('Config save error:', error);
            this.showNotification('Save Failed', error.message, 'error');
        }
    }

    addLogEntry(message, type = 'info') {
        const logContainer = document.getElementById('grid-trading-log');
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${type}`;

        logEntry.innerHTML = `
            <span class="log-time">${new Date().toLocaleTimeString()}</span>
            <span class="log-message">${message}</span>
        `;

        logContainer.insertBefore(logEntry, logContainer.firstChild);

        // Keep only last 50 entries
        while (logContainer.children.length > 50) {
            logContainer.removeChild(logContainer.lastChild);
        }
    }

    clearTradingLog() {
        document.getElementById('grid-trading-log').innerHTML = `
            <div class="log-entry">
                <span class="log-time">${new Date().toLocaleTimeString()}</span>
                <span class="log-message">Trading log cleared</span>
            </div>
        `;
    }

    showNotification(title, message, type = 'info') {
        // Use existing notification system if available
        if (typeof showNotification === 'function') {
            showNotification(title, message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${title} - ${message}`);
        }
    }

    startAutoRefresh() {
        // Check status every 30 seconds
        this.gridStatusInterval = setInterval(() => {
            if (this.isGridActive) {
                this.checkGridStatus();
            }
        }, 30000);

        // Performance update every 60 seconds
        this.performanceInterval = setInterval(() => {
            if (this.isGridActive) {
                this.updatePerformanceMetrics();
            }
        }, 60000);
    }

    async updatePerformanceMetrics() {
        try {
            const response = await fetch('/api/grid/performance');
            const result = await response.json();

            if (result.status === 'success') {
                const performance = result.performance;

                // Log significant milestones
                if (performance.overview.completed_cycles > 0 &&
                    performance.overview.completed_cycles % 10 === 0) {
                    this.addLogEntry(`🎉 ${performance.overview.completed_cycles} cycles completed!`, 'success');
                }

                // Check if we're hitting targets
                if (performance.targets.progress_to_target >= 100) {
                    this.addLogEntry('🎯 Daily profit target achieved!', 'success');
                }
            }

        } catch (error) {
            console.error('Performance update error:', error);
        }
    }

    destroy() {
        if (this.gridStatusInterval) {
            clearInterval(this.gridStatusInterval);
        }
        if (this.performanceInterval) {
            clearInterval(this.performanceInterval);
        }
    }
}

// Initialize Grid Trading Dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    // Wait a bit for other scripts to load
    setTimeout(() => {
        if (!window.gridDashboard) {
            window.gridDashboard = new GridTradingDashboard();
        }
    }, 1000);
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GridTradingDashboard;
}
