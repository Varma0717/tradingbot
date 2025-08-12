"""
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
