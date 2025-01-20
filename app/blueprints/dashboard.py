from flask import Blueprint, render_template, jsonify, current_app
from flask_login import login_required, current_user
from app.core.models import Farm, Product

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Hlavní stránka s přehledem"""
    try:
        # Získání statistik
        farms = Farm.query.filter_by(user_id=current_user.id).all()
        stats = {
            'farms_count': len(farms),
            'active_farms': len([f for f in farms if f.is_active]),
            'total_products': 0,
            'confirmed_products': 0,
            'recent_activities': []
        }
        
        # Statistiky produktů pro každou farmu
        for farm in farms:
            products = Product.query.filter_by(farm_id=farm.id).all()
            stats['total_products'] += len(products)
            stats['confirmed_products'] += len([p for p in products if p.is_confirmed])
        
        return render_template('dashboard/index.html', stats=stats, farms=farms)
        
    except Exception as e:
        current_app.logger.error(f'Chyba při načítání dashboardu: {str(e)}')
        return render_template('dashboard/index.html', error=str(e))

@dashboard_bp.route('/stats')
@login_required
def get_stats():
    """API endpoint pro aktualizaci statistik"""
    try:
        farms = Farm.query.filter_by(user_id=current_user.id).all()
        
        # Základní statistiky
        stats = {
            'farms_count': len(farms),
            'active_farms': len([f for f in farms if f.is_active]),
            'products_by_status': {
                'draft': 0,
                'pending': 0,
                'confirmed': 0
            }
        }
        
        # Statistiky produktů
        for farm in farms:
            products = Product.query.filter_by(farm_id=farm.id).all()
            for product in products:
                if product.is_confirmed:
                    stats['products_by_status']['confirmed'] += 1
                else:
                    stats['products_by_status']['draft'] += 1
        
        return jsonify(stats)
        
    except Exception as e:
        current_app.logger.error(f'Chyba při získávání statistik: {str(e)}')
        return jsonify({
            'error': 'Při získávání statistik došlo k chybě'
        }), 500

@dashboard_bp.route('/activities')
@login_required
def get_activities():
    """API endpoint pro získání posledních aktivit"""
    try:
        activities = []
        farms = Farm.query.filter_by(user_id=current_user.id).all()
        
        for farm in farms:
            farm_activities = Product.query.filter_by(farm_id=farm.id).all()
            activities.extend(farm_activities)
        
        # Seřazení a formátování aktivit
        activities.sort(key=lambda x: x.created_at, reverse=True)
        activities = [a.to_dict() for a in activities[:10]]
        
        return jsonify(activities)
        
    except Exception as e:
        current_app.logger.error(f'Chyba při získávání aktivit: {str(e)}')
        return jsonify({
            'error': 'Při získávání aktivit došlo k chybě'
        }), 500 