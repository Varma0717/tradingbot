"""
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
