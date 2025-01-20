from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for, flash
from flask_login import login_required, current_user
from app.core.models import Farm
from app import db
import os
import json
import csv
import io

farms_bp = Blueprint('farms', __name__)

# Vytvoření adresáře pro data farem při inicializaci blueprintu
@farms_bp.before_app_request
def setup_farm_directory():
    """Vytvoření adresáře pro data farem"""
    farm_base_dir = os.path.join(current_app.root_path, 'data', 'farms')
    os.makedirs(farm_base_dir, exist_ok=True)
    current_app.logger.info(f'Vytvořen základní adresář pro farmy: {farm_base_dir}')

@farms_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Registrace nové farmy"""
    current_app.logger.info(f'Přístup k registraci farmy - metoda {request.method}')
    
    if request.method == 'GET':
        current_app.logger.debug('Zobrazení formuláře pro registraci farmy')
        return render_template('farms/register.html')
    
    try:
        current_app.logger.info('Pokus o registraci nové farmy')
        # Získání dat z formuláře
        farm_id = request.form.get('farm_id')
        name = request.form.get('name')
        description = request.form.get('description')
        csv_file = request.files.get('products_csv')

        # Validace povinných polí
        if not all([farm_id, name, description, csv_file]):
            missing_fields = [field for field, value in {
                'farm_id': farm_id,
                'name': name,
                'description': description,
                'products_csv': csv_file
            }.items() if not value]
            current_app.logger.warning(f'Chybí povinná pole: {", ".join(missing_fields)}')
            flash(f'Chybí povinná pole: {", ".join(missing_fields)}', 'danger')
            return redirect(url_for('farms.register'))

        # Kontrola existence farmy se stejným ID
        existing_farm = Farm.query.filter_by(farm_id=farm_id).first()
        if existing_farm:
            current_app.logger.warning(f'Farma s ID {farm_id} již existuje')
            flash(f'Farma s ID {farm_id} již existuje', 'danger')
            return redirect(url_for('farms.register'))

        try:
            # Vytvoření adresáře pro farmu
            farm_dir = os.path.join(current_app.root_path, 'data', 'farms', farm_id)
            os.makedirs(farm_dir, exist_ok=True)
            current_app.logger.debug(f'Vytvořen adresář pro farmu: {farm_dir}')

            # Čtení a zpracování CSV souboru
            csv_content = csv_file.read().decode('utf-8')
            current_app.logger.debug(f'Přečteno {len(csv_content)} bytů z CSV souboru')
            
            try:
                reader = csv.DictReader(io.StringIO(csv_content))
                csv_data = [row for row in reader]
                current_app.logger.debug(f'Načteno {len(csv_data)} řádků z CSV')
                current_app.logger.debug(f'CSV hlavičky: {reader.fieldnames}')
            except Exception as csv_error:
                current_app.logger.error(f'Chyba při parsování CSV: {str(csv_error)}', exc_info=True)
                flash('Chyba při zpracování CSV souboru. Zkontrolujte formát a strukturu souboru.', 'danger')
                return redirect(url_for('farms.register'))
            
            if not csv_data:
                current_app.logger.warning('CSV soubor je prázdný nebo neobsahuje validní data')
                flash('CSV soubor je prázdný nebo neobsahuje validní data', 'danger')
                return redirect(url_for('farms.register'))

            # Vytvoření JSON souboru s daty farmy
            farm_data = {
                'farm_id': farm_id,
                'name': name,
                'description': description,
                'products': csv_data
            }
            
            json_path = os.path.join(farm_dir, f'{farm_id}.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(farm_data, f, ensure_ascii=False, indent=2)
            current_app.logger.debug(f'Uložena data farmy do: {json_path}')

        except Exception as e:
            current_app.logger.error(f'Chyba při zpracování souborů: {str(e)}', exc_info=True)
            flash('Chyba při zpracování souborů. Zkontrolujte formát CSV souboru.', 'danger')
            return redirect(url_for('farms.register'))

        # Vytvoření záznamu v databázi
        farm = Farm(
            farm_id=farm_id,
            name=name,
            description=description,
            user_id=current_user.id
        )
        
        db.session.add(farm)
        db.session.commit()
        current_app.logger.info(f'Farma {name} byla úspěšně vytvořena (ID: {farm_id})')
        
        flash('Farma byla úspěšně zaregistrována', 'success')
        return redirect(url_for('farms.list'))
        
    except Exception as e:
        current_app.logger.error(f'Chyba při registraci farmy: {str(e)}', exc_info=True)
        flash('Při registraci farmy došlo k chybě', 'danger')
        return redirect(url_for('farms.register'))

@farms_bp.route('/list')
@login_required
def list():
    """Seznam farem uživatele"""
    current_app.logger.info('Přístup k seznamu farem')
    
    try:
        # Získání farem uživatele
        farms = Farm.query.filter_by(user_id=current_user.id).all()
        current_app.logger.debug(f'Nalezeno {len(farms)} farem pro uživatele {current_user.id}')
        
        # Načtení počtu produktů pro každou farmu
        for farm in farms:
            try:
                json_path = os.path.join(current_app.root_path, 'data', 'farms', farm.farm_id, f'{farm.farm_id}.json')
                if os.path.exists(json_path):
                    with open(json_path, 'r', encoding='utf-8') as f:
                        farm_data = json.load(f)
                        # Počítáme pouze řádky dat bez hlavičky
                        farm.products = farm_data.get('products', [])
                        current_app.logger.debug(f'Načteno {len(farm.products)} produktů pro farmu {farm.farm_id}')
                else:
                    farm.products = []
                    current_app.logger.warning(f'JSON soubor pro farmu {farm.farm_id} neexistuje: {json_path}')
            except Exception as e:
                farm.products = []
                current_app.logger.error(f'Chyba při načítání JSON dat pro farmu {farm.farm_id}: {str(e)}', exc_info=True)
        
        return render_template('farms/list.html', farms=farms)
        
    except Exception as e:
        current_app.logger.error(f'Chyba při načítání seznamu farem: {str(e)}', exc_info=True)
        flash('Při načítání seznamu farem došlo k chybě', 'danger')
        return redirect(url_for('index'))

@farms_bp.route('/<string:farm_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(farm_id):
    """Úprava farmy"""
    current_app.logger.info(f'Přístup k úpravě farmy {farm_id} - metoda {request.method}')
    
    try:
        # Získání farmy podle farm_id
        farm = Farm.query.filter_by(farm_id=farm_id).first_or_404()
        current_app.logger.debug(f'Načtena farma: {farm.name}')
        
        # Kontrola přístupu
        if farm.user_id != current_user.id:
            current_app.logger.warning(f'Pokus o neoprávněný přístup k farmě {farm_id} uživatelem {current_user.id}')
            flash('Nemáte přístup k této farmě', 'danger')
            return redirect(url_for('farms.list'))
        
        if request.method == 'GET':
            return render_template('farms/edit.html', farm=farm)
        
        # Aktualizace farmy
        farm.name = request.form.get('name')
        farm.description = request.form.get('description')
        
        # Zpracování CSV souboru, pokud byl nahrán
        if 'products_csv' in request.files:
            csv_file = request.files['products_csv']
            if csv_file and csv_file.filename:
                try:
                    # Načtení a zpracování CSV
                    csv_content = csv_file.read().decode('utf-8')
                    reader = csv.DictReader(io.StringIO(csv_content))
                    csv_data = [row for row in reader]
                    
                    if csv_data:
                        # Aktualizace JSON souboru s daty farmy
                        farm_dir = os.path.join(current_app.root_path, 'data', 'farms', farm_id)
                        os.makedirs(farm_dir, exist_ok=True)
                        
                        farm_data = {
                            'farm_id': farm_id,
                            'name': farm.name,
                            'description': farm.description,
                            'products': csv_data
                        }
                        
                        json_path = os.path.join(farm_dir, f'{farm_id}.json')
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(farm_data, f, ensure_ascii=False, indent=2)
                        current_app.logger.info(f'Aktualizován seznam produktů pro farmu {farm_id}')
                except Exception as e:
                    current_app.logger.error(f'Chyba při zpracování CSV souboru: {str(e)}', exc_info=True)
                    return jsonify({
                        'success': False,
                        'message': 'Chyba při zpracování CSV souboru'
                    }), 400
        
        db.session.commit()
        current_app.logger.info(f'Farma {farm.name} byla úspěšně aktualizována')
        
        return jsonify({
            'success': True,
            'message': 'Farma byla úspěšně aktualizována',
            'redirect_url': url_for('farms.list')
        })
        
    except Exception as e:
        current_app.logger.error(f'Chyba při úpravě farmy {farm_id}: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': 'Při úpravě farmy došlo k chybě'
        }), 500

@farms_bp.route('/<string:farm_id>/delete', methods=['POST'])
@login_required
def delete(farm_id):
    """Smazání farmy"""
    current_app.logger.info(f'Pokus o smazání farmy {farm_id}')
    
    try:
        # Získání farmy podle farm_id
        farm = Farm.query.filter_by(farm_id=farm_id).first()
        
        if not farm:
            current_app.logger.warning(f'Farma {farm_id} nebyla nalezena')
            return jsonify({
                'success': False,
                'message': 'Farma nebyla nalezena'
            }), 404
        
        # Kontrola přístupu
        if farm.user_id != current_user.id:
            current_app.logger.warning(f'Pokus o neoprávněný přístup k farmě {farm_id} uživatelem {current_user.id}')
            return jsonify({
                'success': False,
                'message': 'Nemáte přístup k této farmě'
            }), 403
        
        # Smazání adresáře farmy
        farm_dir = os.path.join(current_app.root_path, 'data', 'farms', farm_id)
        if os.path.exists(farm_dir):
            import shutil
            try:
                shutil.rmtree(farm_dir)
                current_app.logger.info(f'Smazán adresář farmy: {farm_dir}')
            except Exception as e:
                current_app.logger.error(f'Chyba při mazání adresáře farmy {farm_id}: {str(e)}', exc_info=True)
                return jsonify({
                    'success': False,
                    'message': 'Chyba při mazání adresáře farmy'
                }), 500
        
        # Smazání záznamu z databáze
        db.session.delete(farm)
        db.session.commit()
        current_app.logger.info(f'Farma {farm_id} byla úspěšně smazána')
        
        return jsonify({
            'success': True,
            'message': 'Farma byla úspěšně smazána'
        })
        
    except Exception as e:
        current_app.logger.error(f'Chyba při mazání farmy {farm_id}: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': 'Při mazání farmy došlo k chybě'
        }), 500 