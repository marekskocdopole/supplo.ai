import os
import csv
from typing import List, Dict, Optional
from werkzeug.utils import secure_filename
from app import db
from app.core.models import Farm, Product
from app.config.config import Config

class FarmManager:
    def __init__(self):
        self.upload_folder = Config.UPLOAD_FOLDER
        
    def create_farm(self, farm_data: dict, user_id: int) -> Farm:
        """Vytvoří novou farmu"""
        farm = Farm(
            farm_id=farm_data['farm_id'],
            name=farm_data['name'],
            description=farm_data.get('description'),
            address=farm_data.get('address'),
            contact_email=farm_data.get('contact_email'),
            contact_phone=farm_data.get('contact_phone'),
            user_id=user_id
        )
        
        db.session.add(farm)
        db.session.commit()
        
        # Vytvoření adresářové struktury
        farm_path = os.path.join(self.upload_folder, farm.farm_id)
        os.makedirs(farm_path, exist_ok=True)
        os.makedirs(os.path.join(farm_path, 'images'), exist_ok=True)
        
        return farm
    
    def get_farm(self, farm_id: str) -> Optional[Farm]:
        """Načte farmu podle ID"""
        return Farm.query.filter_by(farm_id=farm_id).first()
    
    def get_user_farms(self, user_id: int) -> List[Farm]:
        """Vrátí seznam farem uživatele"""
        return Farm.query.filter_by(user_id=user_id).all()
    
    def update_farm(self, farm_id: str, data: dict) -> bool:
        """Aktualizuje data farmy"""
        farm = self.get_farm(farm_id)
        if not farm:
            return False
            
        for key, value in data.items():
            if hasattr(farm, key):
                setattr(farm, key, value)
                
        db.session.commit()
        return True
    
    def delete_farm(self, farm_id: str) -> bool:
        """Smaže farmu a všechna její data"""
        farm = self.get_farm(farm_id)
        if not farm:
            return False
            
        # Smazání adresářové struktury
        farm_path = os.path.join(self.upload_folder, farm.farm_id)
        if os.path.exists(farm_path):
            for root, dirs, files in os.walk(farm_path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(farm_path)
            
        db.session.delete(farm)
        db.session.commit()
        return True
    
    def process_csv(self, farm_id: str, csv_file) -> List[Dict]:
        """Zpracuje CSV soubor s produkty"""
        farm = self.get_farm(farm_id)
        if not farm:
            raise ValueError("Farma neexistuje")
            
        # Uložení původního CSV
        filename = secure_filename(csv_file.filename)
        csv_path = os.path.join(self.upload_folder, farm.farm_id, 'original.csv')
        csv_file.save(csv_path)
        
        products = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                product = Product(
                    farm_id=farm.id,
                    sku=row['Shop SKU'],
                    name=row['Name'],
                    original_description=row.get('Description', ''),
                    ingredients=row.get('Farm ingredients', ''),
                    metadata_dict={'farm_description': row.get('Farm Description', '')}
                )
                products.append(product)
                
        db.session.bulk_save_objects(products)
        db.session.commit()
        
        return [p.to_dict() for p in products] 