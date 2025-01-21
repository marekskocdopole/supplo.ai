import os
import json
from typing import List, Dict, Optional
from werkzeug.utils import secure_filename
from app import db
from app.core.models import Product, Farm
from app.config.config import Config
from app.generators.text_generator import TextGenerator, GenerationError
from flask import current_app

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
            current_app.logger.info(f"Začátek ukládání obrázku pro farmu {farm_id}, SKU {sku}")
            
            # Načtení JSON souboru
            json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'farms', farm_id, f'{farm_id}.json')
            current_app.logger.info(f"Cesta k JSON souboru: {json_path}")
            
            if not os.path.exists(json_path):
                current_app.logger.error(f"JSON soubor pro farmu {farm_id} neexistuje")
                raise ValueError(f"JSON soubor pro farmu {farm_id} neexistuje")
            
            with open(json_path, 'r', encoding='utf-8') as f:
                farm_data = json.load(f)
                current_app.logger.info("JSON soubor úspěšně načten")
            
            # Najít produkt
            for product in farm_data.get('products', []):
                if product.get('Shop SKU') == sku:
                    current_app.logger.info(f"Nalezen produkt s SKU {sku}")
                    
                    # Vytvoření cesty pro obrázek
                    images_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'farms', farm_id, f'{farm_id}_images')
                    os.makedirs(images_dir, exist_ok=True)
                    current_app.logger.info(f"Adresář pro obrázky: {images_dir}")
                    
                    # Uložení obrázku
                    filename = f"{sku}.jpg"
                    image_path = os.path.join(images_dir, filename)
                    image_file.save(image_path)
                    current_app.logger.info(f"Obrázek uložen do: {image_path}")
                    
                    # Vždy použijeme produkční URL pro ukládání do JSONu
                    server_url = "http://161.35.70.99/products"
                    image_url = f"{server_url}/{farm_id}_images/{filename}"
                    current_app.logger.info(f"Vytvořena URL obrázku: {image_url}")
                    
                    # Uložení KOMPLETNÍ URL do JSONu
                    old_url = product.get('mirakl_image_1', '')
                    product['mirakl_image_1'] = image_url
                    product['image_path'] = image_url  # Ukládáme stejnou URL i do image_path
                    current_app.logger.info(f"Stará URL: {old_url}")
                    current_app.logger.info(f"Nová URL uložena do JSONu: {image_url}")
                    
                    # Uložení změn do JSONu
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(farm_data, f, ensure_ascii=False, indent=2)
                    current_app.logger.info("Změny úspěšně uloženy do JSONu")
                    
                    # Pro lokální prostředí vrátíme lokální URL pro zobrazení v prohlížeči
                    if os.environ.get('FLASK_ENV') == 'development':
                        return f"http://127.0.0.1:5001/products/{farm_id}_images/{filename}"
                    
                    # V produkci vrátíme stejnou URL jako je v JSONu
                    return image_url
            
            raise ValueError(f"Produkt {sku} nebyl nalezen v JSON souboru")
            
        except Exception as e:
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