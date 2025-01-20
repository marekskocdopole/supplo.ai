import os
import json

def update_image_urls():
    """Aktualizuje URL obrázků v JSON souborech na kompletní URL"""
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'farms')
    
    for farm_id in os.listdir(base_dir):
        json_path = os.path.join(base_dir, farm_id, f'{farm_id}.json')
        if os.path.exists(json_path):
            print(f"Zpracovávám farmu {farm_id}...")
            
            # Načtení JSON souboru
            with open(json_path, 'r', encoding='utf-8') as f:
                farm_data = json.load(f)
            
            # Aktualizace URL obrázků
            for product in farm_data.get('products', []):
                if 'mirakl_image_1' in product:
                    current_path = product['mirakl_image_1']
                    if not current_path.startswith('http'):
                        # Extrahujeme název souboru z cesty
                        filename = os.path.basename(current_path)
                        # Vytvoříme novou URL
                        new_url = f"http://161.35.70.99/products/{farm_id}_images/{filename}"
                        product['mirakl_image_1'] = new_url
            
            # Uložení aktualizovaného JSONu
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(farm_data, f, ensure_ascii=False, indent=2)
            
            print(f"Farma {farm_id} byla aktualizována.")

if __name__ == '__main__':
    update_image_urls() 