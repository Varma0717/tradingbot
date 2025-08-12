// Unified Dashboard JavaScript - Enhanced UI Version
// CSRF Token helper function
function getCSRFToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (!metaTag) {
        console.error('CSRF token meta tag not found');
        return '';
    }
    const token = metaTag.getAttribute('content');
    console.log('CSRF Token:', token ? 'Found' : 'Not found');
    return token;
}

// Authentication check function
function checkAuthentication() {
    // Simple check to see if user is authenticated
    return fetch('/user/api/bot-status', { method: 'HEAD' })
        .then(response => {
            if (response.status === 401 || response.status === 302) {
                console.warn('User not authenticated');
                showNotification('Please log in to access dashboard features', 'warning');
                return false;
            }
            return true;
        })
        .catch(() => {
            console.warn('Unable to check authentication status');
            return false;
        });
}

// Throttling mechanism to prevent excessive API calls
let isUpdating = false;
let lastUpdateTime = 0;
const MIN_UPDATE_INTERVAL = 5000; // Minimum 5 seconds between updates

// UI Enhancement functions
function updateLastUpdateTime() {
    const lastUpdateElement = document.getElementById('last-update');
    if (lastUpdateElement) {
        const now = new Date();
        lastUpdateElement.textContent = `Last Updated: ${now.toLocaleTimeString()}`;
    }
}

function updateQuickStatus(message) {
    const quickStatusElement = document.getElementById('quick-status');
    if (quickStatusElement) {
        quickStatusElement.textContent = message;
    }
}

function updateTradingModeIndicator(isLive) {
    const indicator = document.getElementById('trading-mode-indicator');
    const modeText = document.getElementById('current-mode');

    if (indicator && modeText) {
        if (isLive) {
            indicator.className = 'w-4 h-4 rounded-full bg-red-500 shadow-lg animate-pulse';
            modeText.textContent = 'Live Trading';
        } else {
            indicator.className = 'w-4 h-4 rounded-full bg-blue-500 shadow-lg';
            modeText.textContent = 'Paper Trading';
        }
    }

    // Update the mode display in bot panel
    const currentTradingMode = document.getElementById('current-trading-mode');
    if (currentTradingMode) {
        if (isLive) {
            currentTradingMode.innerHTML = '<span class="w-2 h-2 bg-red-500 rounded-full mr-2"></span>Live Trading Mode';
            currentTradingMode.className = 'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800';
        } else {
            currentTradingMode.innerHTML = '<span class="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>Paper Trading Mode';
            currentTradingMode.className = 'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800';
        }
    }
}

function updateBotStatusIndicators(stockRunning, cryptoRunning) {
    // Update individual bot status indicators
    const stockIndicator = document.getElementById('stock-status-indicator');
    const cryptoIndicator = document.getElementById('crypto-status-indicator');

    if (stockIndicator) {
        stockIndicator.className = `w-3 h-3 rounded-full ${stockRunning ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`;
    }

    if (cryptoIndicator) {
        cryptoIndicator.className = `w-3 h-3 rounded-full ${cryptoRunning ? 'bg-orange-500 animate-pulse' : 'bg-gray-400'}`;
    }

    // Update overall status
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

function showHideBotButtons(stockRunning, cryptoRunning) {
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

// Real-time data update functions
function updateDashboardData() {
    // Throttle updates to prevent rate limiting
    const now = Date.now();
    if (isUpdating || (now - lastUpdateTime) < MIN_UPDATE_INTERVAL) {
        console.log('Update throttled - too many requests');
        return;
    }

    isUpdating = true;
    lastUpdateTime = now;
    updateQuickStatus('Updating...');

    // Update portfolio summary and bot status simultaneously
    const portfolioPromise = fetch('/user/api/portfolio-summary')
        .then(response => {
            console.log('Portfolio summary response status:', response.status);
            if (!response.ok) {
                if (response.status === 302 || response.status === 401) {
                    console.warn('User not authenticated - redirected to login');
                    showNotification('Please log in to view dashboard data', 'warning');
                    return null;
                }
                throw new Error(`Portfolio API error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (!data) return; // Handle authentication failure
            if (data.success) {
                const portfolioValue = document.getElementById('portfolio-value');
                const dailyPnl = document.getElementById('daily-pnl');
                const dailyPnlPercent = document.getElementById('daily-pnl-percent');
                const activeTrades = document.getElementById('active-trades');
                const portfolioChange = document.getElementById('portfolio-change');

                if (portfolioValue) portfolioValue.textContent = `$${Number(data.total_value || 0).toLocaleString()}`;
                if (dailyPnl) dailyPnl.textContent = `$${Number(data.daily_pnl || 0).toLocaleString()}`;

                if (dailyPnlPercent) {
                    const dailyPnlPercentValue = data.daily_pnl_percent || 0;
                    const pnlText = `${dailyPnlPercentValue >= 0 ? '+' : ''}${dailyPnlPercentValue.toFixed(2)}%`;
                    dailyPnlPercent.innerHTML = `<span class="${dailyPnlPercentValue >= 0 ? 'text-green-600' : 'text-red-600'}">${pnlText}</span>`;
                }

                if (portfolioChange) {
                    const changeValue = data.portfolio_change || 0;
                    const changePercent = data.portfolio_change_percent || 0;
                    const changeText = `${changeValue >= 0 ? '+' : ''}$${Math.abs(changeValue).toLocaleString()} (${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%)`;
                    portfolioChange.innerHTML = `<span class="${changeValue >= 0 ? 'text-green-600' : 'text-red-600'}">${changeText}</span>`;
                }

                if (activeTrades) activeTrades.textContent = data.positions_count || '0';
            }
        })
        .catch(error => {
            console.error('Portfolio summary error:', error);
            showNotification('Failed to update portfolio data', 'error');
        });

    const botStatusPromise = fetch('/user/api/bot-status')
        .then(response => {
            console.log('Bot status response status:', response.status);
            if (!response.ok) {
                if (response.status === 302 || response.status === 401) {
                    console.warn('User not authenticated for bot status');
                    return null;
                }
                throw new Error(`Bot status API error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (!data) return; // Handle authentication failure
            if (data.success) {
                const stockRunning = data.stock_bot?.is_running || false;
                const cryptoRunning = data.crypto_bot?.is_running || false;

                // Update bot status text with enhanced messaging
                const stockBotStatus = document.getElementById('stock-bot-status');
                const cryptoBotStatus = document.getElementById('crypto-bot-status');
                const botStatus = document.getElementById('bot-status');

                if (stockBotStatus) {
                    if (stockRunning) {
                        const uptime = data.stock_bot?.uptime || 'Just started';
                        stockBotStatus.textContent = `Running • ${uptime}`;
                        stockBotStatus.className = 'text-sm font-medium text-green-600';
                    } else {
                        stockBotStatus.textContent = 'Inactive • Ready to start';
                        stockBotStatus.className = 'text-sm font-medium text-gray-500';
                    }
                }

                if (cryptoBotStatus) {
                    if (cryptoRunning) {
                        const uptime = data.crypto_bot?.uptime || 'Just started';
                        cryptoBotStatus.textContent = `Running • ${uptime}`;
                        cryptoBotStatus.className = 'text-sm font-medium text-orange-600';
                    } else {
                        cryptoBotStatus.textContent = 'Inactive • Ready to start';
                        cryptoBotStatus.className = 'text-sm font-medium text-gray-500';
                    }
                }

                // Use enhanced UI functions
                updateBotStatusIndicators(stockRunning, cryptoRunning);
                showHideBotButtons(stockRunning, cryptoRunning);

                // Update overall bot status card
                if (botStatus) {
                    const overallStatus = stockRunning || cryptoRunning ? 'Active' : 'Inactive';
                    botStatus.textContent = overallStatus;
                    botStatus.className = `text-2xl font-bold ${stockRunning || cryptoRunning ? 'text-green-600' : 'text-gray-400'}`;
                }

                // Update trading mode if available
                if (data.trading_mode) {
                    updateTradingModeIndicator(data.trading_mode === 'live');

                    // Update toggle switch
                    const tradingModeToggle = document.getElementById('trading-mode-toggle');
                    if (tradingModeToggle) {
                        tradingModeToggle.checked = data.trading_mode === 'live';
                    }
                }

                // Update overall bot status
                if (botStatus) {
                    const overallStatus = stockRunning || cryptoRunning ? 'Active' : 'Inactive';
                    botStatus.textContent = overallStatus;
                }

                // Update daily P&L from bot data if available
                const totalPnl = (data.stock_bot?.daily_pnl || 0) + (data.crypto_bot?.daily_pnl || 0);
                if (totalPnl !== 0) {
                    const dailyPnl = document.getElementById('daily-pnl');
                    if (dailyPnl) dailyPnl.textContent = `$${Number(totalPnl).toLocaleString()}`;
                }
            }
        })
        .catch(error => {
            console.error('Bot status error:', error);
            showNotification('Failed to update bot status', 'error');
        });

    // Wait for both promises to complete before resetting throttling
    Promise.allSettled([portfolioPromise, botStatusPromise])
        .finally(() => {
            // Reset throttling flag
            isUpdating = false;
            updateLastUpdateTime();
            updateQuickStatus('Dashboard Ready');
        });

    // Portfolio tabs will be updated manually by user clicks to avoid rate limiting
}

// Function to update portfolio summary display
function updatePortfolioSummary(data) {
    // Update total value
    if (data.total_value !== undefined) {
        const totalValueElement = document.querySelector('.text-2xl.font-bold.text-gray-900');
        if (totalValueElement) {
            totalValueElement.textContent = `$${Number(data.total_value || 0).toLocaleString()}`;
        }
    }

    // Update daily P&L
    if (data.daily_pnl !== undefined) {
        const pnlElements = document.querySelectorAll('.text-sm');
        pnlElements.forEach(element => {
            if (element.textContent.includes('$') && element.textContent.includes('%')) {
                const pnl = Number(data.daily_pnl || 0);
                const pnlPercent = Number(data.daily_pnl_percent || 0);
                element.textContent = `${pnl >= 0 ? '+' : ''}$${pnl.toLocaleString()} (${pnlPercent >= 0 ? '+' : ''}${pnlPercent.toFixed(2)}%)`;
                element.className = `text-sm ${pnl >= 0 ? 'text-green-600' : 'text-red-600'}`;
            }
        });
    }
}

// Bot control functions
function startStockBot() {
    fetch('/user/automation/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
        },
        body: JSON.stringify({})
    })
        .then(response => {
            if (!response.ok) throw new Error('Stock bot start API error');
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showNotification('Stock bot started successfully', 'success');
                // Update will happen automatically via throttled interval
            } else {
                showNotification(data.message || 'Failed to start stock bot', 'error');
            }
        })
        .catch(error => {
            console.error('Start stock bot error:', error);
            showNotification('Failed to start stock bot', 'error');
        });
}

function startCryptoBot() {
    fetch('/user/automation/start-crypto', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
        },
        body: JSON.stringify({})
    })
        .then(response => {
            if (!response.ok) throw new Error('Crypto bot start API error');
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showNotification('Crypto bot started successfully', 'success');
                // Update will happen automatically via throttled interval
            } else {
                showNotification(data.message || 'Failed to start crypto bot', 'error');
            }
        })
        .catch(error => {
            console.error('Start crypto bot error:', error);
            showNotification('Failed to start crypto bot', 'error');
        });
}

function stopStockBot() {
    fetch('/user/automation/stop', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json',
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Stock bot stopped', 'info');
                // Update will happen automatically via throttled interval
            }
        })
        .catch(error => {
            console.error('Stop stock bot error:', error);
            showNotification('Failed to stop stock bot', 'error');
        });
}

function stopCryptoBot() {
    fetch('/user/automation/stop-crypto', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json',
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Crypto bot stopped', 'info');
                // Update will happen automatically via throttled interval
            }
        })
        .catch(error => {
            console.error('Stop crypto bot error:', error);
            showNotification('Failed to stop crypto bot', 'error');
        });
}

function stopAllBots() {
    // Stop stock bot
    fetch('/user/automation/stop', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json',
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Stock bot stopped');
            }
        })
        .catch(console.error);

    // Stop crypto bot
    fetch('/user/automation/stop-crypto', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json',
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Crypto bot stopped');
            }
        })
        .catch(console.error);

    showNotification('All bots stopped', 'info');
    // Update will happen automatically via throttled interval
}

function updateTradingMode(mode) {
    fetch('/user/preferences/api', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ trading_mode: mode })
    })
        .then(response => {
            if (!response.ok) throw new Error('Trading mode API error');
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showNotification(`Switched to ${mode} trading mode`, 'info');
                // Update will happen automatically via throttled interval
            } else {
                showNotification(data.error || 'Failed to update trading mode', 'error');
            }
        })
        .catch(error => {
            console.error('Trading mode error:', error);
            showNotification('Failed to update trading mode', 'error');
        });
}

// AI Functions
function loadAISignals(aiEnabled = false) {
    if (aiEnabled) {
        fetch('/user/api/ai/signals')
            .then(response => {
                if (!response.ok) throw new Error('AI signals API error');
                return response.json();
            })
            .then(data => {
                const container = document.getElementById('ai-signals-preview');
                if (data.success && data.signals && data.signals.length > 0) {
                    container.innerHTML = data.signals.slice(0, 3).map(signal => `
            <div class="flex justify-between items-center p-2 bg-${signal.action === 'BUY' ? 'green' : signal.action === 'SELL' ? 'red' : 'yellow'}-50 rounded">
              <span class="text-sm font-medium">${signal.symbol} - ${signal.action}</span>
              <span class="text-xs" style="color: ${signal.action === 'BUY' ? '#16a34a' : signal.action === 'SELL' ? '#dc2626' : '#ca8a04'};">${signal.confidence}%</span>
            </div>
          `).join('');
                } else {
                    container.innerHTML = '<p class="text-gray-500 text-center py-2">No AI signals available</p>';
                }
            })
            .catch(error => {
                console.error('AI signals error:', error);
                const container = document.getElementById('ai-signals-preview');
                if (container) {
                    container.innerHTML = '<p class="text-red-500 text-center py-2">Error loading AI signals</p>';
                }
            });
    } else {
        const container = document.getElementById('ai-signals-preview');
        if (container) {
            container.innerHTML = '<p class="text-gray-500 text-center py-2">AI features not enabled</p>';
        }
    }
}

function optimizePortfolio() {
    // This function will be implemented based on Flask route availability
    console.log('Portfolio optimization requested');
}

function getMarketAnalysis() {
    // This function will be implemented based on Flask route availability
    console.log('Market analysis requested');
}

function showNotification(message, type = 'info') {
    // Enhanced notification system with better styling
    const notification = document.createElement('div');

    let bgColor = 'bg-blue-500';
    let icon = '🔔';

    switch (type) {
        case 'success':
            bgColor = 'bg-green-500';
            icon = '✅';
            break;
        case 'error':
            bgColor = 'bg-red-500';
            icon = '❌';
            break;
        case 'warning':
            bgColor = 'bg-yellow-500';
            icon = '⚠️';
            break;
        default:
            bgColor = 'bg-blue-500';
            icon = 'ℹ️';
    }

    notification.className = `fixed top-4 right-4 p-4 rounded-lg text-white z-50 ${bgColor} shadow-lg max-w-sm`;
    notification.innerHTML = `
        <div class="flex items-center space-x-2">
            <span class="text-lg">${icon}</span>
            <span class="flex-1">${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="text-white hover:text-gray-200 ml-2">×</button>
        </div>
    `;

    document.body.appendChild(notification);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Portfolio loading functions to avoid rate limiting
function loadLivePortfolio() {
    fetch('/user/api/portfolio?mode=live', {
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
        .then(response => {
            console.log('Live portfolio response status:', response.status);
            if (!response.ok) {
                if (response.status === 302 || response.status === 401) {
                    console.warn('User not authenticated for live portfolio');
                    throw new Error('Please log in to view live portfolio');
                }
                throw new Error(`Live portfolio API error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Live portfolio data:', data);
            const container = document.getElementById('live-holdings');
            if (!container) {
                console.warn('Live holdings container not found');
                return;
            }

            if (data.success && data.positions && data.positions.length > 0) {
                container.innerHTML = data.positions.map(position => `
        <div class="flex justify-between items-center p-3 bg-gray-50 rounded">
          <div>
            <p class="font-medium">${position.symbol}</p>
            <p class="text-sm text-gray-500">${position.quantity} shares</p>
          </div>
          <div class="text-right">
            <p class="font-medium">$${Number(position.current_value || 0).toLocaleString()}</p>
            <p class="text-sm ${(position.pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'}">${(position.pnl || 0) >= 0 ? '+' : ''}$${Number(position.pnl || 0).toLocaleString()}</p>
          </div>
        </div>
      `).join('');
            } else {
                container.innerHTML = '<p class="text-gray-500 text-center py-4">No live holdings</p>';
            }
        })
        .catch(error => {
            console.error('Live portfolio error:', error);
            const container = document.getElementById('live-holdings');
            if (container) {
                container.innerHTML = `<p class="text-red-500 text-center py-4">Error: ${error.message}</p>`;
            }
            showNotification(`Live portfolio error: ${error.message}`, 'error');
        });
}

function loadPaperPortfolio() {
    fetch('/user/api/portfolio?mode=paper', {
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
        .then(response => {
            console.log('Paper portfolio response status:', response.status);
            if (!response.ok) {
                if (response.status === 302 || response.status === 401) {
                    console.warn('User not authenticated for paper portfolio');
                    throw new Error('Please log in to view paper portfolio');
                }
                throw new Error(`Paper portfolio API error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Paper portfolio data:', data);
            const container = document.getElementById('paper-holdings');
            if (!container) {
                console.warn('Paper holdings container not found');
                return;
            }

            if (data.success && data.positions && data.positions.length > 0) {
                container.innerHTML = data.positions.map(position => `
        <div class="flex justify-between items-center p-3 bg-gray-50 rounded">
          <div>
            <p class="font-medium">${position.symbol}</p>
            <p class="text-sm text-gray-500">${position.quantity} shares</p>
          </div>
          <div class="text-right">
            <p class="font-medium">$${Number(position.current_value || 0).toLocaleString()}</p>
            <p class="text-sm ${(position.pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'}">${(position.pnl || 0) >= 0 ? '+' : ''}$${Number(position.pnl || 0).toLocaleString()}</p>
          </div>
        </div>
      `).join('');
            } else {
                container.innerHTML = '<p class="text-gray-500 text-center py-4">No paper holdings</p>';
            }
        })
        .catch(error => {
            console.error('Paper portfolio error:', error);
            const container = document.getElementById('paper-holdings');
            if (container) {
                container.innerHTML = `<p class="text-red-500 text-center py-4">Error: ${error.message}</p>`;
            }
            showNotification(`Paper portfolio error: ${error.message}`, 'error');
        });
}

function loadTradeHistory() {
    // Placeholder for trade history loading
    console.log('Loading trade history...');
}

function loadRecentActivity() {
    fetch('/user/api/recent-activity', {
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
        .then(response => {
            console.log('Recent activity response status:', response.status);
            if (!response.ok) {
                if (response.status === 302 || response.status === 401) {
                    console.warn('User not authenticated for recent activity');
                    throw new Error('Please log in to view recent activity');
                }
                throw new Error(`Recent activity API error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Recent activity data:', data);
            const container = document.getElementById('recent-trades');
            if (!container) {
                console.warn('Recent trades container not found');
                return;
            }

            if (data.success && data.recent_trades && data.recent_trades.length > 0) {
                container.innerHTML = data.recent_trades.slice(0, 5).map(trade => `
        <div class="flex justify-between items-center p-3 bg-gray-50 rounded">
          <div>
            <p class="font-medium">${trade.symbol}</p>
            <p class="text-sm text-gray-500">${trade.side.toUpperCase()} ${trade.quantity}</p>
          </div>
          <div class="text-right">
            <p class="font-medium">$${Number(trade.price || 0).toFixed(2)}</p>
            <p class="text-sm text-gray-500">${new Date(trade.timestamp).toLocaleTimeString()}</p>
          </div>
        </div>
      `).join('');
            } else {
                container.innerHTML = '<p class="text-gray-500 text-center py-4">No recent trades</p>';
            }
        })
        .catch(error => {
            console.error('Recent trades error:', error);
            const container = document.getElementById('recent-trades');
            if (container) {
                container.innerHTML = `<p class="text-red-500 text-center py-4">Error: ${error.message}</p>`;
            }
            showNotification(`Recent activity error: ${error.message}`, 'error');
        });
}

// Initialize dashboard functionality
function initializeDashboard(config = {}) {
    const { aiEnabled = false } = config;

    // Add tab switching event listeners
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', function () {
            const tabName = this.getAttribute('data-tab');

            // Remove active class from all buttons and tabs
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active', 'border-blue-500', 'text-blue-600');
                btn.classList.add('border-transparent', 'text-gray-500');
            });
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.add('hidden');
            });

            // Add active class to clicked button
            this.classList.add('active', 'border-blue-500', 'text-blue-600');
            this.classList.remove('border-transparent', 'text-gray-500');

            // Show corresponding tab
            const targetTab = document.getElementById(tabName + '-tab');
            if (targetTab) {
                targetTab.classList.remove('hidden');

                // Load data for the selected tab to avoid rate limiting
                if (tabName === 'live') {
                    loadLivePortfolio();
                } else if (tabName === 'paper') {
                    loadPaperPortfolio();
                } else if (tabName === 'history') {
                    loadTradeHistory();
                }
            }
        });
    });

    // Initialize dashboard
    updateDashboardData();
    if (aiEnabled) {
        loadAISignals(true);
    }

    // Set up real-time updates (reduced frequency to avoid rate limiting)
    const updateInterval = setInterval(updateDashboardData, 60000); // Update every 60 seconds

    // Load recent activity less frequently
    setInterval(loadRecentActivity, 120000); // Update recent activity every 2 minutes

    // Load recent activity on initial load
    setTimeout(loadRecentActivity, 2000);

    // Bot control buttons - with null checks
    const stockBotStart = document.getElementById('stock-bot-start');
    const cryptoBotStart = document.getElementById('crypto-bot-start');
    const stockBotStop = document.getElementById('stock-bot-stop');
    const cryptoBotStop = document.getElementById('crypto-bot-stop');
    const stopAllBtn = document.getElementById('stop-all-bots');
    const tradingModeSelect = document.getElementById('trading-mode');
    const tradingModeToggle = document.getElementById('trading-mode-toggle');

    if (stockBotStart) stockBotStart.addEventListener('click', startStockBot);
    if (cryptoBotStart) cryptoBotStart.addEventListener('click', startCryptoBot);
    if (stockBotStop) stockBotStop.addEventListener('click', stopStockBot);
    if (cryptoBotStop) cryptoBotStop.addEventListener('click', stopCryptoBot);
    if (stopAllBtn) stopAllBtn.addEventListener('click', stopAllBots);

    // Trading mode selector
    if (tradingModeSelect) {
        tradingModeSelect.addEventListener('change', (e) => {
            updateTradingMode(e.target.value);
        });
    }

    // Enhanced Trading mode toggle switch
    if (tradingModeToggle) {
        tradingModeToggle.addEventListener('change', (e) => {
            const mode = e.target.checked ? 'live' : 'paper';
            updateTradingMode(mode);
            updateTradingModeIndicator(e.target.checked);
        });
    }

    // Trading mode radio buttons
    document.querySelectorAll('input[name="mode"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            const mode = e.target.value;
            updateTradingMode(mode);
        });
    });

    // Initialize trading mode indicator
    updateTradingModeIndicator(false); // Default to paper trading

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        clearInterval(updateInterval);
    });
}

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if this is the dashboard page
    if (document.getElementById('portfolio-value') || document.getElementById('bot-status')) {
        // Get AI enabled status from a data attribute or meta tag
        const aiEnabledMeta = document.querySelector('meta[name="ai-enabled"]');
        const aiEnabled = aiEnabledMeta ? aiEnabledMeta.getAttribute('content') === 'true' : false;

        initializeDashboard({ aiEnabled });
    }
});
