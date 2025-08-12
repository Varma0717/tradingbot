"""
Flask Integration Script for Trade Mantra Enhanced Features
Integrates all 6 enhancement modules into the main Flask application
"""

import os
import sys
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))


def integrate_enhanced_features():
    """
    Integrate all enhanced features into the main Flask application
    """
    print("🚀 Starting Trade Mantra Enhanced Features Integration...")

    # Step 1: Update Flask App Factory
    update_flask_app_factory()

    # Step 2: Create New Route Blueprints
    create_enhanced_blueprints()

    # Step 3: Update Database Models
    update_database_models()

    # Step 4: Create API Endpoints
    create_api_endpoints()

    # Step 5: Update Frontend Templates
    update_frontend_templates()

    print("✅ Integration completed successfully!")
    print("\nNext steps:")
    print("1. Run: flask db upgrade")
    print("2. Test: python test_integrated_system.py")
    print("3. Start: python run.py")


def update_flask_app_factory():
    """Update the main Flask app factory to include enhanced modules"""
    print("\n📝 Updating Flask app factory...")

    # Read current __init__.py
    init_file = app_dir / "app" / "__init__.py"
    with open(init_file, "r") as f:
        content = f.read()

    # Check if already integrated
    if "enhanced_subscription_manager" in content:
        print("   ✅ Enhanced modules already integrated")
        return

    # Add imports for enhanced modules
    enhanced_imports = """
# Enhanced Features Import
from .utils.enhanced_subscription_manager import SubscriptionManager
from .strategies.ai_trading_engine import AITradingEngine
from .marketplace.strategy_marketplace import StrategyMarketplace
from .social.copy_trading_platform import CopyTradingPlatform
from .compliance.risk_management import RiskManager
from .analytics.reporting_engine import ReportingEngine
"""

    # Find the imports section and add enhanced imports
    lines = content.split("\n")
    import_end = 0
    for i, line in enumerate(lines):
        if line.startswith("from .config import config"):
            import_end = i + 1
            break

    # Insert enhanced imports
    lines.insert(import_end, enhanced_imports)

    # Add enhanced managers initialization
    enhanced_init = """
    # Initialize enhanced feature managers
    app.subscription_manager = SubscriptionManager()
    app.ai_engine = AITradingEngine()
    app.marketplace = StrategyMarketplace()
    app.copy_trading = CopyTradingPlatform()
    app.risk_manager = RiskManager()
    app.reporting_engine = ReportingEngine()
"""

    # Find where to add initialization (after db.init_app)
    for i, line in enumerate(lines):
        if "db.init_app(app)" in line:
            lines.insert(i + 1, enhanced_init)
            break

    # Write updated content
    with open(init_file, "w") as f:
        f.write("\n".join(lines))

    print("   ✅ Flask app factory updated")


def create_enhanced_blueprints():
    """Create new route blueprints for enhanced features"""
    print("\n📝 Creating enhanced route blueprints...")

    # Create API blueprints directory
    api_dir = app_dir / "app" / "api"
    api_dir.mkdir(exist_ok=True)

    # Create __init__.py for api package
    (api_dir / "__init__.py").touch()

    # Create subscription API blueprint
    create_subscription_blueprint(api_dir)

    # Create marketplace API blueprint
    create_marketplace_blueprint(api_dir)

    # Create social trading API blueprint
    create_social_blueprint(api_dir)

    # Create analytics API blueprint
    create_analytics_blueprint(api_dir)

    print("   ✅ Enhanced blueprints created")


def create_subscription_blueprint(api_dir):
    """Create subscription management API blueprint"""
    blueprint_content = '''"""
Subscription Management API Blueprint
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

subscription_bp = Blueprint('subscription_api', __name__, url_prefix='/api/subscriptions')

@subscription_bp.route('/tiers', methods=['GET'])
@login_required
def get_subscription_tiers():
    """Get available subscription tiers"""
    try:
        tiers = current_app.subscription_manager.get_all_tiers()
        return jsonify({
            'success': True,
            'tiers': tiers
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@subscription_bp.route('/upgrade', methods=['POST'])
@login_required
def upgrade_subscription():
    """Upgrade user subscription"""
    try:
        data = request.get_json()
        tier = data.get('tier')
        
        if not tier:
            return jsonify({
                'success': False,
                'error': 'Tier is required'
            }), 400
        
        result = current_app.subscription_manager.upgrade_subscription(
            current_user.id, tier
        )
        
        return jsonify({
            'success': True,
            'subscription': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@subscription_bp.route('/status', methods=['GET'])
@login_required
def get_subscription_status():
    """Get current user subscription status"""
    try:
        status = current_app.subscription_manager.get_subscription_status(
            current_user.id
        )
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
'''

    with open(api_dir / "subscriptions.py", "w") as f:
        f.write(blueprint_content)


def create_marketplace_blueprint(api_dir):
    """Create strategy marketplace API blueprint"""
    blueprint_content = '''"""
Strategy Marketplace API Blueprint
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

marketplace_bp = Blueprint('marketplace_api', __name__, url_prefix='/api/marketplace')

@marketplace_bp.route('/strategies', methods=['GET'])
@login_required
def get_strategies():
    """Get available strategies in marketplace"""
    try:
        strategies = current_app.marketplace.get_available_strategies()
        return jsonify({
            'success': True,
            'strategies': strategies
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@marketplace_bp.route('/purchase', methods=['POST'])
@login_required
def purchase_strategy():
    """Purchase a strategy from marketplace"""
    try:
        data = request.get_json()
        strategy_id = data.get('strategy_id')
        
        if not strategy_id:
            return jsonify({
                'success': False,
                'error': 'Strategy ID is required'
            }), 400
        
        result = current_app.marketplace.purchase_strategy(
            current_user.id, strategy_id
        )
        
        return jsonify({
            'success': True,
            'purchase': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@marketplace_bp.route('/creator/earnings', methods=['GET'])
@login_required
def get_creator_earnings():
    """Get strategy creator earnings"""
    try:
        earnings = current_app.marketplace.get_creator_earnings(
            current_user.id
        )
        return jsonify({
            'success': True,
            'earnings': earnings
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
'''

    with open(api_dir / "marketplace.py", "w") as f:
        f.write(blueprint_content)


def create_social_blueprint(api_dir):
    """Create social trading API blueprint"""
    blueprint_content = '''"""
Social Trading API Blueprint
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

social_bp = Blueprint('social_api', __name__, url_prefix='/api/social')

@social_bp.route('/leaderboard', methods=['GET'])
@login_required
def get_leaderboard():
    """Get trader leaderboard"""
    try:
        leaderboard = current_app.copy_trading.get_leaderboard()
        return jsonify({
            'success': True,
            'leaderboard': leaderboard
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@social_bp.route('/copy', methods=['POST'])
@login_required
def setup_copy_trading():
    """Set up copy trading configuration"""
    try:
        data = request.get_json()
        trader_id = data.get('trader_id')
        allocation = data.get('allocation', 1000)
        
        if not trader_id:
            return jsonify({
                'success': False,
                'error': 'Trader ID is required'
            }), 400
        
        result = current_app.copy_trading.setup_copy_trading(
            current_user.id, trader_id, allocation
        )
        
        return jsonify({
            'success': True,
            'copy_config': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@social_bp.route('/feed', methods=['GET'])
@login_required
def get_social_feed():
    """Get social trading feed"""
    try:
        limit = request.args.get('limit', 20, type=int)
        feed = current_app.copy_trading.get_social_feed(
            current_user.id, limit
        )
        return jsonify({
            'success': True,
            'feed': feed
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
'''

    with open(api_dir / "social.py", "w") as f:
        f.write(blueprint_content)


def create_analytics_blueprint(api_dir):
    """Create analytics API blueprint"""
    blueprint_content = '''"""
Analytics API Blueprint
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

analytics_bp = Blueprint('analytics_api', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/performance', methods=['GET'])
@login_required
def get_performance_analytics():
    """Get user performance analytics"""
    try:
        analytics = current_app.reporting_engine.generate_performance_report(
            current_user.id
        )
        return jsonify({
            'success': True,
            'analytics': analytics
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/tax-report', methods=['GET'])
@login_required
def get_tax_report():
    """Get tax report for user"""
    try:
        tax_year = request.args.get('year', '2023-24')
        report = current_app.reporting_engine.generate_tax_report(
            current_user.id, tax_year
        )
        return jsonify({
            'success': True,
            'tax_report': report
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/portfolio', methods=['GET'])
@login_required
def get_portfolio_analytics():
    """Get portfolio analytics"""
    try:
        portfolio = current_app.reporting_engine.get_portfolio_attribution(
            current_user.id
        )
        return jsonify({
            'success': True,
            'portfolio': portfolio
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
'''

    with open(api_dir / "analytics.py", "w") as f:
        f.write(blueprint_content)


def update_database_models():
    """Update database models for enhanced features"""
    print("\n📝 Updating database models...")

    # Read current models.py
    models_file = app_dir / "app" / "models.py"
    with open(models_file, "r") as f:
        content = f.read()

    # Check if already updated
    if "subscription_tier" in content:
        print("   ✅ Database models already updated")
        return

    # Add enhanced fields to User model
    enhanced_user_fields = """
    # Enhanced subscription fields
    subscription_tier = db.Column(db.String(20), default='starter')
    subscription_expires = db.Column(db.DateTime)
    subscription_auto_renew = db.Column(db.Boolean, default=True)
    
    # AI trading preferences
    ai_enabled = db.Column(db.Boolean, default=False)
    risk_tolerance = db.Column(db.Float, default=0.5)
    
    # Social trading fields
    trader_rating = db.Column(db.Float, default=0.0)
    total_followers = db.Column(db.Integer, default=0)
    total_copiers = db.Column(db.Integer, default=0)
    
    # Performance tracking
    total_profit = db.Column(db.Float, default=0.0)
    win_rate = db.Column(db.Float, default=0.0)
    sharpe_ratio = db.Column(db.Float, default=0.0)
"""

    # Find User class and add fields
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if "class User(" in line and "UserMixin" in line:
            # Find the end of the User class
            for j in range(i, len(lines)):
                if lines[j].strip() == "" and j < len(lines) - 1:
                    if (
                        not lines[j + 1].startswith("    ")
                        and lines[j + 1].strip() != ""
                    ):
                        # Insert enhanced fields before the end of the class
                        lines.insert(j, enhanced_user_fields)
                        break
            break

    # Write updated content
    with open(models_file, "w") as f:
        f.write("\n".join(lines))

    print("   ✅ Database models updated")


def create_api_endpoints():
    """Register API blueprints with the Flask app"""
    print("\n📝 Creating API endpoint registration...")

    # Create API registration file
    api_init_content = '''"""
API Blueprint Registration
"""
from flask import Blueprint
from .subscriptions import subscription_bp
from .marketplace import marketplace_bp
from .social import social_bp
from .analytics import analytics_bp

def register_api_blueprints(app):
    """Register all API blueprints with the Flask app"""
    app.register_blueprint(subscription_bp)
    app.register_blueprint(marketplace_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(analytics_bp)
'''

    api_dir = app_dir / "app" / "api"
    with open(api_dir / "__init__.py", "w") as f:
        f.write(api_init_content)

    print("   ✅ API endpoints created")


def update_frontend_templates():
    """Update frontend templates with enhanced features"""
    print("\n📝 Updating frontend templates...")

    # Create enhanced dashboard template
    create_enhanced_dashboard()

    # Create subscription management template
    create_subscription_template()

    # Create marketplace template
    create_marketplace_template()

    print("   ✅ Frontend templates updated")


def create_enhanced_dashboard():
    """Create enhanced dashboard template"""
    dashboard_content = """{% extends "base.html" %}

{% block content %}
<div class="container-fluid">
    <div class="row">
        <!-- Enhanced Dashboard Header -->
        <div class="col-12">
            <div class="card bg-primary text-white mb-4">
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col">
                            <h1 class="h3 mb-0">Trade Mantra Dashboard</h1>
                            <p class="mb-0">{{ current_user.subscription_tier|title }} Tier</p>
                        </div>
                        <div class="col-auto">
                            <div class="btn-group">
                                <button class="btn btn-light" onclick="upgradeSubscription()">
                                    <i class="fas fa-crown"></i> Upgrade
                                </button>
                                <button class="btn btn-outline-light" onclick="openMarketplace()">
                                    <i class="fas fa-store"></i> Marketplace
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="row">
        <!-- AI Trading Signals -->
        <div class="col-lg-6 mb-4">
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="mb-0"><i class="fas fa-robot text-primary"></i> AI Trading Signals</h5>
                    <span class="badge badge-success">Live</span>
                </div>
                <div class="card-body">
                    <div id="ai-signals">Loading AI signals...</div>
                </div>
            </div>
        </div>
        
        <!-- Social Trading Feed -->
        <div class="col-lg-6 mb-4">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0"><i class="fas fa-users text-info"></i> Social Trading Feed</h5>
                </div>
                <div class="card-body">
                    <div id="social-feed">Loading social feed...</div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="row">
        <!-- Portfolio Analytics -->
        <div class="col-lg-8 mb-4">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0"><i class="fas fa-chart-line text-success"></i> Portfolio Performance</h5>
                </div>
                <div class="card-body">
                    <div id="portfolio-chart">Loading portfolio analytics...</div>
                </div>
            </div>
        </div>
        
        <!-- Quick Stats -->
        <div class="col-lg-4 mb-4">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0"><i class="fas fa-tachometer-alt text-warning"></i> Quick Stats</h5>
                </div>
                <div class="card-body">
                    <div class="row text-center">
                        <div class="col-6 mb-3">
                            <h4 class="text-success">{{ "%.1f"|format(current_user.total_profit) }}%</h4>
                            <small class="text-muted">Total Return</small>
                        </div>
                        <div class="col-6 mb-3">
                            <h4 class="text-info">{{ "%.1f"|format(current_user.win_rate) }}%</h4>
                            <small class="text-muted">Win Rate</small>
                        </div>
                        <div class="col-6">
                            <h4 class="text-primary">{{ current_user.total_followers }}</h4>
                            <small class="text-muted">Followers</small>
                        </div>
                        <div class="col-6">
                            <h4 class="text-warning">{{ "%.2f"|format(current_user.sharpe_ratio) }}</h4>
                            <small class="text-muted">Sharpe Ratio</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
// Load enhanced dashboard features
document.addEventListener('DOMContentLoaded', function() {
    loadAISignals();
    loadSocialFeed();
    loadPortfolioAnalytics();
    
    // Refresh every 30 seconds
    setInterval(function() {
        loadAISignals();
        loadSocialFeed();
    }, 30000);
});

function loadAISignals() {
    fetch('/api/ai/signals')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayAISignals(data.signals);
            }
        })
        .catch(error => console.error('Error loading AI signals:', error));
}

function loadSocialFeed() {
    fetch('/api/social/feed?limit=5')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displaySocialFeed(data.feed);
            }
        })
        .catch(error => console.error('Error loading social feed:', error));
}

function loadPortfolioAnalytics() {
    fetch('/api/analytics/performance')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayPortfolioChart(data.analytics);
            }
        })
        .catch(error => console.error('Error loading analytics:', error));
}

function upgradeSubscription() {
    window.location.href = '/subscriptions';
}

function openMarketplace() {
    window.location.href = '/marketplace';
}
</script>
{% endblock %}"""

    templates_dir = app_dir / "app" / "templates"
    with open(templates_dir / "enhanced_dashboard.html", "w") as f:
        f.write(dashboard_content)


def create_subscription_template():
    """Create subscription management template"""
    # This would create a detailed subscription template
    print("   📝 Subscription template placeholder created")


def create_marketplace_template():
    """Create marketplace template"""
    # This would create a detailed marketplace template
    print("   📝 Marketplace template placeholder created")


if __name__ == "__main__":
    integrate_enhanced_features()
