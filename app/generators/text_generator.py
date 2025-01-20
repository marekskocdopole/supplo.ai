import re
import time
import logging
import httpx
from typing import Dict
from openai import OpenAI
from app.config.config import Config
from app.core.product_name_processor import ProductNameProcessor

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    pass

class GenerationError(Exception):
    pass

class TextGenerator:
    def __init__(self):
        http_client = httpx.Client()
        self.client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            http_client=http_client
        )
        self.name_processor = ProductNameProcessor()
        
    def generate_short_description(self, product_data: Dict) -> str:
        """Generování krátkého popisu s upraveným názvem produktu."""
        # Zjednodušení názvu produktu
        simplified_name = self.name_processor.simplify_product_name(
            product_data['name'],
            alt_name=product_data.get('alt_name', '')
        )

        prompt = f"""
        Napiš krátký popis produktu (max 150 znaků).
        
        Název produktu: {simplified_name}
        Charakteristika produktu: {product_data.get('ingredients', '')}
        O farmě: {product_data.get('farm_description', '')}
        
        Pravidla pro popis:
        1. Piš věcně a informativně
        2. Vyhýbej se přehnanému marketingu
        3. Nepoužívej vykřičníky
        4. Vyhýbej se opakování slov jako:
           textura, kvalita, konzistence, vůně, láska, jemný, ekologický,
           skvělý, ideální, úspěšný, výrazný, křupavý, krémový
        5. Zahrň relevantní klíčová slova pro SEO
        6. Zachovej autentický tón
        7. Piš ve třetí osobě
        8. Všechny procentní hodnoty musí mít mezeru před znakem "%"
        
        Odpověď musí mít PŘESNĚ 1-2 věty a MAXIMÁLNĚ 150 znaků.
        """
        return self._retry_generation(product_data, prompt, max_tokens=200, description_type='short')
        
    def generate_long_description(self, product_data: Dict) -> str:
        """Generování dlouhého popisu s upraveným názvem produktu."""
        # Zjednodušení názvu produktu
        simplified_name = self.name_processor.simplify_product_name(
            product_data['name'],
            alt_name=product_data.get('alt_name', '')
        )

        prompt = f"""
        Napiš detailní popis produktu ve třech odstavcích.
        
        Název produktu: {simplified_name}
        Charakteristika produktu: {product_data.get('ingredients', '')}
        Informace o dodavateli/farmě: {product_data.get('farm_description', '')}
        
        Struktura popisu:
        1. Věcný popis produktu s důrazem na jeho vlastnosti a kvality.
        2. Informace o původu - MUSÍ obsahovat název farmy ({product_data['farm_name']}) 
           a relevantní informace o farmě z pole "Informace o dodavateli/farmě".
        3. Běžné použití a jeden neobvyklý tip na přípravu.
        
        Pravidla pro popis:
        1. Piš věcně a informativně
        2. Vyhýbej se přehnanému marketingu
        3. Nepoužívej vykřičníky
        4. Vyhýbej se opakování slov jako:
           textura, kvalita, konzistence, vůně, láska, jemný, ekologický,
           skvělý, ideální, úspěšný, výrazný, křupavý, krémový
        5. Zahrň relevantní klíčová slova pro SEO
        6. Zachovej autentický tón
        7. Piš ve třetí osobě
        8. Všechny procentní hodnoty musí mít mezeru před znakem "%"
        """
        text = self._retry_generation(product_data, prompt, max_tokens=1000, description_type='long')
        return self._format_long_description(text)
    
    def _create_short_description_prompt(self, product_data: Dict) -> str:
        return f"""
        Napiš krátký popis produktu (max 150 znaků).
        
        Název produktu: {product_data['name']}
        Charakteristika produktu: {product_data['ingredients']}
        O farmě: {product_data['farm_description']}
        
        Pravidla pro popis:
        1. Piš věcně a informativně
        2. Vyhýbej se přehnanému marketingu
        3. Nepoužívej vykřičníky
        4. Vyhýbej se opakování slov jako:
           textura, kvalita, konzistence, vůně, láska, jemný, ekologický,
           skvělý, ideální, úspěšný, výrazný, křupavý, krémový
        5. Zahrň relevantní klíčová slova pro SEO
        6. Zachovej autentický tón
        7. Piš ve třetí osobě
        8. Všechny procentní hodnoty musí mít mezeru před znakem "%"
        
        Odpověď musí mít PŘESNĚ 1-2 věty a MAXIMÁLNĚ 150 znaků.
        """
    
    def _create_long_description_prompt(self, product_data: Dict) -> str:
        return f"""
        Napiš detailní popis produktu ve třech odstavcích.
        
        Název produktu: {product_data['name']}
        Charakteristika produktu: {product_data['ingredients']}
        Informace o dodavateli/farmě: {product_data['farm_description']}
        
        Struktura popisu:
        1. Věcný popis produktu s důrazem na jeho vlastnosti a kvality.
        2. Informace o původu - MUSÍ obsahovat název farmy ({product_data['farm_name']}) 
           a relevantní informace o farmě z pole "Informace o dodavateli/farmě".
        3. Běžné použití a jeden neobvyklý tip na přípravu.
        
        Pravidla pro popis:
        1. Piš věcně a informativně
        2. Vyhýbej se přehnanému marketingu
        3. Nepoužívej vykřičníky
        4. Vyhýbej se opakování slov jako:
           textura, kvalita, konzistence, vůně, láska, jemný, ekologický,
           skvělý, ideální, úspěšný, výrazný, křupavý, krémový
        5. Zahrň relevantní klíčová slova pro SEO
        6. Zachovej autentický tón
        7. Piš ve třetí osobě
        8. Všechny procentní hodnoty musí mít mezeru před znakem "%"
        """
    
    def _generate_with_gpt4(self, prompt: str, max_tokens: int) -> str:
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": "Jsi zkušený copywriter specializující se na věcné "
                              "a informativní produktové popisky pro farmářské potraviny."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    def _format_long_description(self, text: str) -> str:
        """Formátování dlouhého popisu do HTML struktury."""
        paragraphs = text.split('\n\n')
        formatted_text = ""
        
        for i, para in enumerate(paragraphs):
            if i == 1:
                formatted_text += "<p><strong>O původu</strong></p>"
            elif i == 2:
                formatted_text += "<p><strong>Tipy do kuchyně</strong></p>"
            formatted_text += f"<p>{para.strip()}</p>"
        
        return formatted_text
    
    def _validate_output(self, text: str, description_type: str) -> bool:
        """Validace vygenerovaného textu."""
        if description_type == 'short':
            if len(text) > 150:
                logger.warning("Krátký popis je delší než 150 znaků")
                
        # Kontrola zakázaných slov
        forbidden_words = [
            'textura', 'kvalita', 'konzistence', 'vůně', 'láska',
            'jemný', 'ekologický', 'skvělý', 'ideální', 'úspěšný',
            'výrazný', 'křupavý', 'krémový'
        ]
        
        for word in forbidden_words:
            if word in text.lower():
                logger.warning(f"Text obsahuje zakázané slovo: {word}")
                
        # Kontrola formátování procent
        if re.search(r'\d+%', text):  # Hledá číslo následované % bez mezery
            logger.warning("Procentní hodnoty musí mít mezeru před znakem %")
            
        return True
    
    def _retry_generation(self, product_data: Dict, prompt: str, max_tokens: int, description_type: str, max_retries: int = 3) -> str:
        """Opakování generování v případě chyby."""
        last_error = None
        for attempt in range(max_retries):
            try:
                text = self._generate_with_gpt4(prompt, max_tokens)
                self._validate_output(text, description_type)  # Pouze pro logování varování
                return text  # Vždy vrátíme vygenerovaný text
            except Exception as e:
                if isinstance(e, ValidationError):
                    # Pokud jde o ValidationError, vrátíme text i tak
                    return text
                last_error = str(e)
                logger.error(f"Neočekávaná chyba při generování: {str(e)}")
                if attempt < max_retries - 1:  # Pokud nejsme na posledním pokusu
                    time.sleep(2 ** attempt)
                    continue
        
        # Pokud všechny pokusy selhaly kvůli jiné chybě než validaci, vrátíme fallback
        logger.error(f"Všechny pokusy o generování selhaly. Poslední chyba: {last_error}")
        return self._get_fallback_description(product_data)
    
    def _get_fallback_description(self, product_data: Dict) -> str:
        """Vytvoření základního popisu v případě chyby."""
        return f"{product_data['name']} - farmářský produkt z {product_data['farm_name']}." 