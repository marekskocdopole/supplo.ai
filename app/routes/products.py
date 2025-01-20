from flask import Blueprint, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.core.farm_manager import FarmManager
from app.core.product_manager import ProductManager
from app.generators.text_generator import GenerationError

products_bp = Blueprint('products', __name__)
farm_manager = FarmManager()
product_manager = ProductManager()

@products_bp.route('/api/farms/<farm_id>/products', methods=['GET'])
@login_required
def list_products(farm_id):
    """Seznam produktů farmy"""
    farm = farm_manager.get_farm(farm_id)
    
    if not farm or farm.user_id != current_user.id:
        return jsonify({'error': 'Farma nenalezena'}), 404
        
    include_inactive = request.args.get('include_inactive', '').lower() == 'true'
    products = product_manager.get_farm_products(farm.id, include_inactive)
    
    return jsonify([product.to_dict() for product in products])

@products_bp.route('/api/products/<sku>/image', methods=['POST'])
@login_required
def upload_product_image(sku):
    """Upload obrázku produktu"""
    if 'image' not in request.files:
        return jsonify({'error': 'Chybí obrázek'}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Nebyl vybrán soubor'}), 400
        
    farm_id = request.form.get('farm_id')
    if not farm_id:
        return jsonify({'error': 'Chybí ID farmy'}), 400
        
    farm = farm_manager.get_farm(farm_id)
    if not farm or farm.user_id != current_user.id:
        return jsonify({'error': 'Farma nenalezena'}), 404
        
    # Kontrola typu souboru
    if not file.filename.lower().endswith(tuple(current_app.config['ALLOWED_EXTENSIONS'])):
        return jsonify({'error': 'Nepodporovaný formát souboru'}), 400
        
    image_path = product_manager.save_product_image(farm.id, sku, file)
    if image_path:
        return jsonify({'image_path': image_path})
    return jsonify({'error': 'Uložení obrázku se nezdařilo'}), 400

@products_bp.route('/api/products/generate', methods=['POST'])
@login_required
def generate_product_content():
    """Generování obsahu produktu"""
    data = request.get_json()
    farm_id = data.get('farm_id')
    sku = data.get('sku')
    
    if not farm_id or not sku:
        return jsonify({'error': 'Chybí povinné parametry'}), 400
        
    farm = farm_manager.get_farm(farm_id)
    if not farm or farm.user_id != current_user.id:
        return jsonify({'error': 'Farma nenalezena'}), 404
        
    try:
        result = product_manager.generate_product_content(farm.id, sku)
        return jsonify(result)
    except GenerationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Neočekávaná chyba při generování obsahu'}), 500

@products_bp.route('/api/products/<sku>/confirm', methods=['POST'])
@login_required
def confirm_product(sku):
    """Potvrzení produktu"""
    data = request.get_json()
    farm_id = data.get('farm_id')
    
    if not farm_id:
        return jsonify({'error': 'Chybí ID farmy'}), 400
        
    farm = farm_manager.get_farm(farm_id)
    if not farm or farm.user_id != current_user.id:
        return jsonify({'error': 'Farma nenalezena'}), 404
        
    if product_manager.confirm_product(farm.id, sku):
        return jsonify({'status': 'success'})
    return jsonify({'error': 'Potvrzení se nezdařilo'}), 400

@products_bp.route('/api/products/<sku>/regenerate', methods=['POST'])
@login_required
def regenerate_product_content(sku):
    """Regenerace obsahu produktu"""
    data = request.get_json()
    farm_id = data.get('farm_id')
    
    if not farm_id:
        return jsonify({'error': 'Chybí ID farmy'}), 400
        
    farm = farm_manager.get_farm(farm_id)
    if not farm or farm.user_id != current_user.id:
        return jsonify({'error': 'Farma nenalezena'}), 404
        
    try:
        result = product_manager.generate_product_content(farm.id, sku)
        return jsonify(result)
    except GenerationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Neočekávaná chyba při generování obsahu'}), 500 