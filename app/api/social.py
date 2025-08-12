"""
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
