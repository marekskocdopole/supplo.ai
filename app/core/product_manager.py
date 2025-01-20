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
        """Uloží obrázek produktu"""
        try:
            # Načtení JSON souboru
            if current_app.config['ENV'] == 'production':
                json_path = os.path.join('/var/www/supplo.ai/app/data/farms', farm_id, f'{farm_id}.json')
            else:
                json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'farms', farm_id, f'{farm_id}.json')
            
            with open(json_path, 'r', encoding='utf-8') as f:
                farm_data = json.load(f)
            
            # Najít produkt
            for product in farm_data.get('products', []):
                if product.get('Shop SKU') == sku:
                    # Vytvoření cesty pro obrázek
                    if current_app.config['ENV'] == 'production':
                        images_dir = os.path.join('/var/www/supplo.ai/app/data/farms', farm_id, f'{farm_id}_images')
                    else:
                        images_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'farms', farm_id, f'{farm_id}_images')
                    
                    os.makedirs(images_dir, exist_ok=True)
                    
                    # Uložení obrázku s názvem shop_sku.jpg
                    filename = f"{sku}.jpg"
                    image_path = os.path.join(images_dir, filename)
                    
                    # Uložení souboru
                    image_file.save(image_path)
                    
                    # Aktualizace cesty v JSONu
                    relative_path = os.path.join(f'{farm_id}_images', filename)
                    product['mirakl_image_1'] = relative_path
                    
                    # Uložení JSONu
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(farm_data, f, ensure_ascii=False, indent=2)
                    
                    return relative_path
            
            raise ValueError(f"Produkt {sku} nenalezen")
        except Exception as e:
            raise ValueError(f"Chyba při ukládání obrázku: {str(e)}")
    
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
        return [
            {
                'Shop SKU': p.sku,
                'Name': p.name,
                'Description': p.original_description or '',
                'Farm ingredients': p.ingredients or '',
                'Farm Description': p.metadata_dict.get('farm_description', ''),
                'Short Description': p.short_description or '',
                'Long Description': p.long_description or '',
                'Price': p.price or '',
                'Unit': p.unit or '',
                'Stock': p.stock or 0,
                'Status': 'Active' if p.is_active else 'Inactive',
                'Confirmed': 'Yes' if p.is_confirmed else 'No'
            }
            for p in products
        ] 