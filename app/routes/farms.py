from flask import Blueprint, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.core.farm_manager import FarmManager
from app.core.product_manager import ProductManager
import os

farms_bp = Blueprint('farms', __name__)
farm_manager = FarmManager()
product_manager = ProductManager()

@farms_bp.route('/api/farms', methods=['GET'])
@login_required
def list_farms():
    """Seznam farem uživatele"""
    farms = farm_manager.get_user_farms(current_user.id)
    return jsonify([farm.to_dict() for farm in farms])

@farms_bp.route('/api/farms/register', methods=['POST'])
@login_required
def register_farm():
    """Registrace nové farmy"""
    if 'csv_file' not in request.files:
        return jsonify({'error': 'Chybí CSV soubor'}), 400
        
    file = request.files['csv_file']
    if file.filename == '':
        return jsonify({'error': 'Nebyl vybrán soubor'}), 400
        
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Soubor musí být ve formátu CSV'}), 400
        
    try:
        farm_data = {
            'farm_id': request.form['farm_id'],
            'name': request.form['name'],
            'description': request.form.get('description'),
            'address': request.form.get('address'),
            'contact_email': request.form.get('contact_email'),
            'contact_phone': request.form.get('contact_phone')
        }
        
        # Vytvoření farmy
        farm = farm_manager.create_farm(farm_data, current_user.id)
        
        # Zpracování CSV
        products = farm_manager.process_csv(farm.farm_id, file)
        
        return jsonify({
            'farm_id': farm.farm_id,
            'status': 'success',
            'product_count': len(products)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@farms_bp.route('/api/farms/<farm_id>', methods=['GET'])
@login_required
def get_farm(farm_id):
    """Detail farmy"""
    farm = farm_manager.get_farm(farm_id)
    
    if not farm or farm.user_id != current_user.id:
        return jsonify({'error': 'Farma nenalezena'}), 404
        
    return jsonify(farm.to_dict())

@farms_bp.route('/api/farms/<farm_id>', methods=['PUT'])
@login_required
def update_farm(farm_id):
    """Aktualizace farmy"""
    farm = farm_manager.get_farm(farm_id)
    
    if not farm or farm.user_id != current_user.id:
        return jsonify({'error': 'Farma nenalezena'}), 404
        
    data = request.get_json()
    if farm_manager.update_farm(farm_id, data):
        return jsonify({'status': 'success'})
    return jsonify({'error': 'Aktualizace se nezdařila'}), 400

@farms_bp.route('/api/farms/<farm_id>', methods=['DELETE'])
@login_required
def delete_farm(farm_id):
    """Smazání farmy"""
    farm = farm_manager.get_farm(farm_id)
    
    if not farm or farm.user_id != current_user.id:
        return jsonify({'error': 'Farma nenalezena'}), 404
        
    if farm_manager.delete_farm(farm_id):
        return jsonify({'status': 'success'})
    return jsonify({'error': 'Smazání se nezdařilo'}), 400

@farms_bp.route('/api/farms/<farm_id>/export', methods=['GET'])
@login_required
def export_farm_data(farm_id):
    """Export dat farmy do CSV"""
    farm = farm_manager.get_farm(farm_id)
    
    if not farm or farm.user_id != current_user.id:
        return jsonify({'error': 'Farma nenalezena'}), 404
        
    products_data = product_manager.export_products_csv(farm.id)
    
    if not products_data:
        return jsonify({'error': 'Žádná data k exportu'}), 404
        
    # Vytvoření CSV souboru
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=products_data[0].keys())
    writer.writeheader()
    writer.writerows(products_data)
    
    # Vytvoření response
    from io import BytesIO
    
    mem = BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    output.close()
    
    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'farm_{farm_id}_export.csv'
    ) 