from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from app.core.models import Product, Farm
from app.core.product_manager import ProductManager
from app import db
import os
import json
import pandas as pd
from io import BytesIO

products_bp = Blueprint('products', __name__)
product_manager = ProductManager()

@products_bp.route('/generate_product_content', methods=['GET', 'POST'])
@login_required
def generate_product_content():
    """Generování obsahu pro produkt"""
    current_app.logger.info('Přístup ke generování obsahu produktu')
    
    if request.method == 'GET':
        # Získání seznamu farem uživatele
        farms = Farm.query.filter_by(user_id=current_user.id).all()
        current_app.logger.debug(f'Nalezeno {len(farms)} farem pro uživatele {current_user.id}')
        return render_template('products/generate.html', farms=farms)
    
    try:
        # Získání dat z požadavku
        data = request.get_json()
        current_app.logger.info(f'Přijatá data: {data}')
        
        sku = data.get('sku')
        farm_id = data.get('farm_id')
        
        current_app.logger.info(f'Generování obsahu pro SKU: {sku}, Farm ID: {farm_id}')
        
        if not sku or not farm_id:
            current_app.logger.error('Chybí SKU nebo ID farmy')
            return jsonify({
                'error': 'Chybí SKU nebo ID farmy'
            }), 400
        
        # Kontrola přístupu k farmě
        farm = Farm.query.filter_by(farm_id=farm_id).first_or_404()
        current_app.logger.info(f'Nalezena farma: {farm.name}')
        
        if farm.user_id != current_user.id:
            current_app.logger.error(f'Uživatel {current_user.id} se pokusil přistoupit k farmě {farm_id}')
            return jsonify({
                'error': 'Nemáte přístup k této farmě'
            }), 403
            
        try:
            current_app.logger.info('Začínám generovat obsah pomocí ProductManager')
            result = product_manager.generate_product_content(farm_id, sku)
            current_app.logger.info(f'Obsah úspěšně vygenerován: {result}')
            return jsonify(result)
        except Exception as e:
            current_app.logger.error(f'Chyba při generování obsahu: {str(e)}', exc_info=True)
            return jsonify({
                'error': f'Při generování obsahu došlo k chybě: {str(e)}'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f'Chyba při generování obsahu: {str(e)}', exc_info=True)
        return jsonify({
            'error': 'Při generování obsahu došlo k chybě'
        }), 500

@products_bp.route('/products/regenerate_content', methods=['POST'])
def regenerate_content():
    """Regenerace obsahu produktu"""
    data = request.get_json()
    farm_id = data.get('farm_id')
    sku = data.get('sku')
    content_type = data.get('type')  # 'short' nebo 'long'
    
    if not farm_id or not sku:
        return jsonify({'error': 'Chybí ID farmy nebo SKU'}), 400
        
    try:
        result = product_manager.generate_product_content(farm_id, sku, content_type)
        return jsonify(result)
    except GenerationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Neočekávaná chyba při generování obsahu'}), 500

@products_bp.route('/api/upload_image', methods=['POST'])
@login_required
def upload_image():
    """Nahraje obrázek produktu"""
    try:
        # Kontrola parametrů
        if 'image' not in request.files:
            return jsonify({'error': 'Chybí soubor obrázku'}), 400
            
        if 'farm_id' not in request.form:
            return jsonify({'error': 'Chybí ID farmy'}), 400
            
        if 'sku' not in request.form:
            return jsonify({'error': 'Chybí SKU produktu'}), 400
            
        image_file = request.files['image']
        farm_id = request.form['farm_id']
        sku = request.form['sku']
        
        # Kontrola přístupu k farmě
        farm = Farm.query.filter_by(farm_id=farm_id).first()
        if not farm or farm.user_id != current_user.id:
            return jsonify({'error': 'Nemáte přístup k této farmě'}), 403
        
        # Uložení obrázku
        try:
            image_path = product_manager.save_product_image(farm_id, sku, image_file)
            if not image_path:
                return jsonify({'error': 'Nepodařilo se uložit obrázek'}), 500
            return jsonify({'image_path': image_path})
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
    except Exception as e:
        current_app.logger.error(f'Chyba při nahrávání obrázku: {str(e)}', exc_info=True)
        return jsonify({'error': f'Neočekávaná chyba: {str(e)}'}), 500

@products_bp.route('/api/products/confirm', methods=['POST'])
def confirm_product():
    """Potvrdí produkt"""
    try:
        # Kontrola parametrů
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Chybí data požadavku'}), 400
            
        farm_id = data.get('farm_id')
        if not farm_id:
            return jsonify({'error': 'Chybí ID farmy'}), 400
            
        sku = data.get('sku')
        if not sku:
            return jsonify({'error': 'Chybí SKU produktu'}), 400
            
        short_description = data.get('short_description')
        long_description = data.get('long_description')
        image_path = data.get('image_path')
            
        # Načtení JSON souboru
        json_path = os.path.join(current_app.root_path, 'data', 'farms', farm_id, f'{farm_id}.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            farm_data = json.load(f)
            
        # Nalezení a aktualizace produktu
        for product in farm_data.get('products', []):
            if product.get('Shop SKU') == sku:
                product['Short Description'] = short_description
                product['Description'] = long_description
                product['mirakl_image_1'] = image_path
                product['is_confirmed'] = True
                break
                
        # Uložení změn
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(farm_data, f, indent=2, ensure_ascii=False)
        
        return jsonify({'success': True})
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
        
    except Exception as e:
        return jsonify({'error': f'Neočekávaná chyba: {str(e)}'}), 500

@products_bp.route('/api/farms/<farm_id>/products', methods=['GET'])
@login_required
def get_farm_products(farm_id):
    """Načtení produktů farmy"""
    current_app.logger.info(f'Začátek načítání produktů pro farmu {farm_id}')
    
    try:
        # Kontrola přístupu k farmě
        current_app.logger.debug(f'Hledám farmu s ID {farm_id}')
        farm = Farm.query.filter_by(farm_id=farm_id).first_or_404()
        current_app.logger.debug(f'Farma nalezena: {farm.name}')
        
        if farm.user_id != current_user.id:
            current_app.logger.warning(f'Uživatel {current_user.id} se pokusil přistoupit k farmě {farm_id}, která mu nepatří')
            return jsonify({
                'error': 'Nemáte přístup k této farmě'
            }), 403
        
        # Načtení JSON souboru s produkty
        json_path = os.path.join(current_app.root_path, 'data', 'farms', farm_id, f'{farm_id}.json')
        current_app.logger.debug(f'Cesta k JSON souboru: {json_path}')
        
        if not os.path.exists(json_path):
            current_app.logger.warning(f'JSON soubor pro farmu {farm_id} neexistuje')
            return jsonify([])
            
        current_app.logger.debug('Načítám JSON soubor')
        with open(json_path, 'r', encoding='utf-8') as f:
            farm_data = json.load(f)
            products = farm_data.get('products', [])
            current_app.logger.debug(f'Načteno {len(products)} produktů z JSON souboru')
            
            # Transformace dat pro frontend
            transformed_products = []
            current_app.logger.info(f'Začínám transformaci {len(products)} produktů')
            
            for i, product in enumerate(products):
                current_app.logger.info(f'Zpracovávám produkt {i+1}/{len(products)}:')
                current_app.logger.info(f'Produkt: {product}')
                
                # Přeskočení hlavičkového řádku (detekce podle hodnot)
                is_header = all([
                    product.get('Category') == 'category',
                    product.get('Shop SKU') == 'shop_sku',
                    product.get('Name') == 'name',
                    product.get('Description') == 'description',
                    product.get('Short Description') == 'short_description',
                    product.get('Weight') == 'weight'
                ])
                
                if is_header:
                    current_app.logger.info('Detekován hlavičkový řádek, přeskakuji')
                    continue
                
                current_app.logger.info(f'Transformuji produkt: {product.get("Shop SKU")} - {product.get("Name")}')
                transformed_product = {
                    'sku': product.get('Shop SKU', ''),
                    'name': product.get('Name', ''),
                    'short_description': product.get('Short Description', ''),
                    'long_description': product.get('Description', ''),
                    'image_path': product.get('mirakl_image_1', ''),
                    'is_confirmed': False,
                    'metadata': {
                        'allergens': product.get('Farm allergens', ''),
                        'ingredients': product.get('Farm ingredients', ''),
                        'weight': product.get('Weight', ''),
                        'category': product.get('Category', '')
                    }
                }
                current_app.logger.info(f'Transformovaný produkt: {transformed_product}')
                transformed_products.append(transformed_product)
                current_app.logger.info(f'Produkt {i+1} úspěšně zpracován')
            
            current_app.logger.info(f'Úspěšně načteno a transformováno {len(transformed_products)} produktů pro farmu {farm_id}')
            return jsonify(transformed_products)
            
    except Exception as e:
        current_app.logger.error(f'Chyba při načítání produktů pro farmu {farm_id}: {str(e)}', exc_info=True)
        return jsonify({
            'error': 'Při načítání produktů došlo k chybě'
        }), 500

@products_bp.route('/api/products/<sku>/regenerate', methods=['POST'])
def regenerate_product_content(sku):
    data = request.get_json()
    farm_id = data.get('farm_id')
    content_type = data.get('type')

    if not farm_id:
        return jsonify({'error': 'Chybí farm_id'}), 400

    try:
        product_manager = ProductManager()
        content = product_manager.generate_product_content(farm_id, sku)
        
        if content_type == 'short':
            return jsonify({'short_description': content['short_description']})
        elif content_type == 'long':
            return jsonify({'long_description': content['long_description']})
        else:
            return jsonify(content)
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f'Chyba při regeneraci obsahu: {str(e)}')
        return jsonify({'error': 'Interní chyba serveru'}), 500

@products_bp.route('/api/farms/<farm_id>/export', methods=['GET'])
def export_farm_data(farm_id):
    try:
        # Načtení JSON souboru
        json_path = os.path.join(current_app.root_path, 'data', 'farms', farm_id, f'{farm_id}.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Získání pouze potvrzených produktů
        products = [p for p in data['products'] if p.get('is_confirmed', False)]
        
        if not products:
            return jsonify({'error': 'Žádné potvrzené produkty k exportu'}), 400
        
        # Vytvoření DataFrame
        df = pd.DataFrame(products)
        
        # Formát exportu
        export_format = request.args.get('format', 'csv')
        
        if export_format == 'excel':
            # Export do Excel
            output = BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'farm_{farm_id}_export.xlsx'
            )
        else:
            # Export do CSV
            output = BytesIO()
            df.to_csv(output, index=False, encoding='utf-8')
            output.seek(0)
            return send_file(
                output,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'farm_{farm_id}_export.csv'
            )
            
    except Exception as e:
        current_app.logger.error(f'Chyba při exportu dat: {str(e)}')
        return jsonify({'error': f'Chyba při exportu dat: {str(e)}'}), 500 