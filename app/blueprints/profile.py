from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.managers.user_manager import UserManager

profile_bp = Blueprint('profile', __name__)
user_manager = UserManager()

@profile_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Nastavení uživatelského profilu"""
    if request.method == 'GET':
        return render_template('profile/settings.html')
    
    try:
        data = request.get_json()
        update_type = data.get('update_type')
        
        if update_type == 'profile':
            # Validace povinných polí
            required_fields = ['first_name', 'last_name', 'email']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({
                        'error': f'Pole {field} je povinné'
                    }), 400
            
            # Aktualizace profilu
            user = user_manager.update_user_profile(
                user_id=current_user.id,
                profile_data={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'email': data['email'],
                    'phone': data.get('phone', ''),
                    'company': data.get('company', ''),
                    'notifications_enabled': data.get('notifications_enabled', True)
                }
            )
            
            return jsonify({
                'message': 'Profil byl úspěšně aktualizován'
            })
            
        elif update_type == 'password':
            # Validace hesel
            current_password = data.get('current_password')
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')
            
            if not all([current_password, new_password, confirm_password]):
                return jsonify({
                    'error': 'Všechna hesla jsou povinná'
                }), 400
            
            if new_password != confirm_password:
                return jsonify({
                    'error': 'Nová hesla se neshodují'
                }), 400
            
            if not check_password_hash(current_user.password_hash, current_password):
                return jsonify({
                    'error': 'Současné heslo není správné'
                }), 400
            
            # Aktualizace hesla
            user_manager.update_user_password(
                user_id=current_user.id,
                new_password=new_password
            )
            
            return jsonify({
                'message': 'Heslo bylo úspěšně změněno'
            })
            
        else:
            return jsonify({
                'error': 'Neplatný typ aktualizace'
            }), 400
            
    except Exception as e:
        current_app.logger.error(f'Chyba při aktualizaci profilu: {str(e)}')
        return jsonify({
            'error': 'Při aktualizaci profilu došlo k chybě'
        }), 500

@profile_bp.route('/delete', methods=['POST'])
@login_required
def delete_account():
    """Smazání uživatelského účtu"""
    try:
        data = request.get_json()
        password = data.get('password')
        
        if not password:
            return jsonify({
                'error': 'Heslo je povinné'
            }), 400
        
        if not check_password_hash(current_user.password_hash, password):
            return jsonify({
                'error': 'Heslo není správné'
            }), 400
        
        # Smazání účtu
        user_manager.delete_user(current_user.id)
        
        return jsonify({
            'message': 'Účet byl úspěšně smazán',
            'redirect_url': url_for('auth.login')
        })
        
    except Exception as e:
        current_app.logger.error(f'Chyba při mazání účtu: {str(e)}')
        return jsonify({
            'error': 'Při mazání účtu došlo k chybě'
        }), 500

@profile_bp.route('/export', methods=['POST'])
@login_required
def export_data():
    """Export uživatelských dat"""
    try:
        # Export dat
        data = user_manager.export_user_data(current_user.id)
        
        return jsonify({
            'data': data,
            'message': 'Data byla úspěšně exportována'
        })
        
    except Exception as e:
        current_app.logger.error(f'Chyba při exportu dat: {str(e)}')
        return jsonify({
            'error': 'Při exportu dat došlo k chybě'
        }), 500 