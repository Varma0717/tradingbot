"""
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
