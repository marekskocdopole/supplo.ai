import os
import json
from typing import List, Dict, Optional
from werkzeug.utils import secure_filename
from app import db
from app.core.models import Product, Farm
from app.config.config import Config
from app.generators.text_generator import TextGenerator, GenerationError

class ProductManager:
    def __init__(self):
        self.upload_folder = Config.UPLOAD_FOLDER
        self.text_generator = TextGenerator()
        
    def get_product(self, farm_id: str, sku: str) -> Optional[dict]:
        """Načte produkt podle SKU a farmy"""
        # Načtení JSON souboru s produkty pro konkrétní farmu
        json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'farms', farm_id, f'{farm_id}.json')
        
        print(f"Hledám soubor: {json_path}")
        
        if not os.path.exists(json_path):
            print(f"Soubor nenalezen na cestě: {json_path}")
            raise ValueError(f"Data farmy {farm_id} nenalezena v {json_path}")
        
        print(f"Soubor nalezen, načítám data...")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            farm_data = json.load(f)
            products = farm_data.get('products', [])
            
            print(f"Načteno {len(products)} produktů")
            print(f"Hledám produkt s SKU: {sku}")
            
            # Najít produkt podle SKU
            for product in products:
                current_sku = product.get('Shop SKU')
                print(f"Kontroluji produkt s SKU: {current_sku}")
                
                # Přeskočit šablonu
                if current_sku == 'shop_sku':
                    print("Přeskakuji šablonu")
                    continue
                    
                if current_sku == sku:
                    print(f"Produkt nalezen: {product.get('Name')}")
                    return product
                    
            print(f"Produkt s SKU {sku} nebyl nalezen")
            raise ValueError(f"Produkt {sku} nenalezen ve farmě {farm_id}")
    
    def get_farm_products(self, farm_id: int, include_inactive: bool = False) -> List[Product]:
        """Vrátí seznam produktů farmy"""
        query = Product.query.filter_by(farm_id=farm_id)
        if not include_inactive:
            query = query.filter_by(is_active=True)
        return query.all()
    
    def update_product(self, farm_id: int, sku: str, data: dict) -> bool:
        """Aktualizuje data produktu"""
        product = self.get_product(farm_id, sku)
        if not product:
            return False
            
        for key, value in data.items():
            if hasattr(product, key):
                setattr(product, key, value)
                
        db.session.commit()
        return True
    
    def delete_product(self, farm_id: int, sku: str) -> bool:
        """Smaže produkt"""
        product = self.get_product(farm_id, sku)
        if not product:
            return False
            
        # Smazání obrázku produktu
        if product.get('image_path'):
            image_path = os.path.join(self.upload_folder, product['image_path'])
            if os.path.exists(image_path):
                os.remove(image_path)
                
        db.session.delete(product)
        db.session.commit()
        return True
    
    def save_product_image(self, farm_id: str, sku: str, image_file) -> Optional[str]:
        """Uloží obrázek produktu a vrátí kompletní URL"""
        try:
            from flask import current_app
            current_app.logger.info(f"=== ZAČÁTEK UKLÁDÁNÍ OBRÁZKU ===")
            current_app.logger.info(f"Farm ID: {farm_id}, SKU: {sku}")
            
            # Načtení JSON souboru - použijeme absolutní cestu z app.root_path
            json_path = os.path.join(current_app.root_path, 'data', 'farms', farm_id, f'{farm_id}.json')
            current_app.logger.info(f"Cesta k JSON: {json_path}")
            
            if not os.path.exists(json_path):
                current_app.logger.error(f"JSON soubor neexistuje: {json_path}")
                raise ValueError(f"JSON soubor pro farmu {farm_id} neexistuje")
            
            with open(json_path, 'r', encoding='utf-8') as f:
                farm_data = json.load(f)
                current_app.logger.info(f"JSON soubor úspěšně načten")
            
            # Najít produkt
            product_found = False
            for product in farm_data.get('products', []):
                if product.get('Shop SKU') == sku:
                    product_found = True
                    current_app.logger.info(f"Nalezen produkt {sku}")
                    
                    # Vytvoření cesty pro obrázek - použijeme absolutní cestu z app.root_path
                    images_dir = os.path.join(current_app.root_path, 'data', 'farms', farm_id, f'{farm_id}_images')
                    os.makedirs(images_dir, exist_ok=True)
                    current_app.logger.info(f"Vytvořen adresář pro obrázky: {images_dir}")
                    
                    # Uložení obrázku
                    filename = f"{sku}.jpg"
                    image_path = os.path.join(images_dir, filename)
                    current_app.logger.info(f"Cesta pro uložení obrázku: {image_path}")
                    
                    # Kontrola typu souboru
                    if not image_file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        current_app.logger.error(f"Nepodporovaný formát souboru: {image_file.filename}")
                        raise ValueError("Nepodporovaný formát souboru. Povolené formáty jsou: JPG, PNG, GIF")
                    
                    # Uložení souboru
                    try:
                        image_file.save(image_path)
                        current_app.logger.info(f"Obrázek úspěšně uložen do: {image_path}")
                    except Exception as e:
                        current_app.logger.error(f"Chyba při ukládání souboru: {str(e)}")
                        raise ValueError(f"Chyba při ukládání souboru: {str(e)}")
                    
                    # VŽDY použít produkční URL pro ukládání do JSONu
                    base_url = "http://161.35.70.99"
                    current_app.logger.info(f"Použita produkční URL: {base_url}")
                    
                    # Vytvoření kompletní URL pro obrázek
                    image_url = f"{base_url}/products/{farm_id}_images/{filename}"
                    current_app.logger.info(f"Vytvořena URL obrázku: {image_url}")
                    
                    # Debug výpis před aktualizací
                    current_app.logger.info(f"Původní hodnoty v JSONu:")
                    current_app.logger.info(f"mirakl_image_1: {product.get('mirakl_image_1')}")
                    current_app.logger.info(f"image_path: {product.get('image_path')}")
                    
                    # Aktualizace všech polí v JSONu, která mohou obsahovat URL obrázku
                    product['mirakl_image_1'] = image_url
                    product['image_path'] = image_url
                    current_app.logger.info(f"Aktualizovány URL v produktu {sku}")
                    
                    # Debug výpis po aktualizaci
                    current_app.logger.info(f"Nové hodnoty v JSONu:")
                    current_app.logger.info(f"mirakl_image_1: {product['mirakl_image_1']}")
                    current_app.logger.info(f"image_path: {product['image_path']}")
                    
                    # Uložit aktualizovaná data zpět do JSON souboru
                    try:
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(farm_data, f, ensure_ascii=False, indent=2)
                        current_app.logger.info(f"Aktualizovaná data byla uložena do JSON souboru: {json_path}")
                    except Exception as e:
                        current_app.logger.error(f"Chyba při ukládání do JSON: {str(e)}")
                        raise ValueError(f"Chyba při ukládání do JSON: {str(e)}")
                    
                    # Projít všechny existující produkty a aktualizovat jejich URL
                    updated_count = 0
                    for p in farm_data.get('products', []):
                        # Debug výpis pro každý produkt
                        current_app.logger.info(f"Kontrola produktu {p.get('Shop SKU')}:")
                        current_app.logger.info(f"Původní mirakl_image_1: {p.get('mirakl_image_1')}")
                        current_app.logger.info(f"Původní image_path: {p.get('image_path')}")
                        
                        # Kontrola a aktualizace URL pro všechny produkty
                        if 'mirakl_image_1' in p and p['mirakl_image_1']:
                            if not p['mirakl_image_1'].startswith('http'):
                                p['mirakl_image_1'] = f"{base_url}/products/{farm_id}_images/{p['Shop SKU']}.jpg"
                                updated_count += 1
                            elif 'localhost' in p['mirakl_image_1'] or '127.0.0.1' in p['mirakl_image_1']:
                                p['mirakl_image_1'] = f"{base_url}/products/{farm_id}_images/{p['Shop SKU']}.jpg"
                                updated_count += 1
                        
                        if 'image_path' in p and p['image_path']:
                            if not p['image_path'].startswith('http'):
                                p['image_path'] = f"{base_url}/products/{farm_id}_images/{p['Shop SKU']}.jpg"
                                updated_count += 1
                            elif 'localhost' in p['image_path'] or '127.0.0.1' in p['image_path']:
                                p['image_path'] = f"{base_url}/products/{farm_id}_images/{p['Shop SKU']}.jpg"
                                updated_count += 1
                            
                        current_app.logger.info(f"Nové mirakl_image_1: {p.get('mirakl_image_1')}")
                        current_app.logger.info(f"Nové image_path: {p.get('image_path')}")
                    
                    # Uložit všechny změny do JSONu
                    if updated_count > 0:
                        try:
                            with open(json_path, 'w', encoding='utf-8') as f:
                                json.dump(farm_data, f, ensure_ascii=False, indent=2)
                            current_app.logger.info(f"Aktualizováno {updated_count} URL v JSON souboru")
                        except Exception as e:
                            current_app.logger.error(f"Chyba při ukládání do JSON: {str(e)}")
                            raise ValueError(f"Chyba při ukládání do JSON: {str(e)}")
                    
                    current_app.logger.info(f"=== KONEC UKLÁDÁNÍ OBRÁZKU ===")
                    return image_url
            
            if not product_found:
                current_app.logger.error(f"Produkt {sku} nebyl nalezen v JSON")
                raise ValueError(f"Produkt {sku} nebyl nalezen v JSON souboru")
            
        except Exception as e:
            current_app.logger.error(f"Chyba při ukládání obrázku: {str(e)}")
            raise ValueError(f"Chyba při ukládání obrázku: {str(e)}")
        
        return None
    
    def confirm_product(self, farm_id: str, sku: str) -> bool:
        """Potvrdí produkt"""
        try:
            # Načtení JSON souboru
            json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'farms', farm_id, f'{farm_id}.json')
            with open(json_path, 'r', encoding='utf-8') as f:
                farm_data = json.load(f)
            
            # Najít produkt
            for product in farm_data.get('products', []):
                if product.get('Shop SKU') == sku:
                    # Nastavení potvrzení
                    product['is_confirmed'] = True
                    
                    # Uložení JSONu
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(farm_data, f, ensure_ascii=False, indent=2)
                    
                    return True
            
            raise ValueError(f"Produkt {sku} nenalezen")
            
        except Exception as e:
            raise ValueError(f"Chyba při potvrzování produktu: {str(e)}")
    
    def generate_product_content(self, farm_id: str, sku: str, content_type: str = None) -> dict:
        """Generování obsahu pro produkt"""
        try:
            product = self.get_product(farm_id, sku)
            
            # Načtení dat o farmě ze stejného souboru
            json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'farms', farm_id, f'{farm_id}.json')
            
            with open(json_path, 'r', encoding='utf-8') as f:
                farm_data = json.load(f)
                
            product_data = {
                'name': product.get('Name', ''),
                'ingredients': product.get('Farm ingredients', ''),
                'farm_description': farm_data.get('description', 'Rodinná farma s tradicí.'),
                'farm_name': farm_data.get('name', farm_id)
            }
            
            # Generování popisků podle typu
            if content_type == 'short':
                return {
                    'short_description': self.text_generator.generate_short_description(product_data)
                }
            elif content_type == 'long':
                return {
                    'long_description': self.text_generator.generate_long_description(product_data)
                }
            else:
                # Generování obou popisků
                short_desc = self.text_generator.generate_short_description(product_data)
                long_desc = self.text_generator.generate_long_description(product_data)
                
                return {
                    'long_description': long_desc,
                    'short_description': short_desc
                }
                
        except Exception as e:
            raise GenerationError(f"Chyba při generování obsahu: {str(e)}")
    
    def bulk_update_products(self, products_data: List[Dict]) -> bool:
        """Hromadná aktualizace produktů"""
        try:
            for data in products_data:
                product = self.get_product(data['farm_id'], data['sku'])
                if product:
                    for key, value in data.items():
                        if hasattr(product, key):
                            setattr(product, key, value)
                            
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False
    
    def export_products_csv(self, farm_id: int) -> List[Dict]:
        """Exportuje produkty do formátu pro CSV"""
        products = self.get_farm_products(farm_id, include_inactive=True)
        
        # Získání farm_id (string) z databáze
        farm = Farm.query.get(farm_id)
        if not farm:
            return []
            
        result = []
        for p in products:
            # Kontrola jestli už máme kompletní URL
            image_url = p.image_path
            if image_url and not image_url.startswith('http'):
                image_url = f"http://161.35.70.99/products/{farm.farm_id}_images/{p.sku}.jpg"
                
            result.append({
                'Shop SKU': p.sku,
                'Name': p.name,
                'Description': p.original_description or '',
                'Farm ingredients': p.ingredients or '',
                'Farm Description': p.metadata_dict.get('farm_description', ''),
                'Short Description': p.short_description or '',
                'Long Description': p.long_description or '',
                'mirakl_image_1': image_url or '',  # Použijeme kompletní URL
                'Price': p.price or '',
                'Unit': p.unit or '',
                'Stock': p.stock or 0,
                'Status': 'Active' if p.is_active else 'Inactive',
                'Confirmed': 'Yes' if p.is_confirmed else 'No'
            })
            
        return result 