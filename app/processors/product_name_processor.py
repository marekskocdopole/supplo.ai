import re
import logging
from typing import Dict, Optional
from openai import OpenAI
from app.config.config import Config

logger = logging.getLogger(__name__)

class ProductNameProcessor:
    def __init__(self):
        self._translation_cache = {}  # Cache pro překlady
        self._product_type_cache = {} # Cache pro typy produktů
        self.client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url="https://api.openai.com/v1"
        )
        
    def _simplify_product_name(self, product_name: str, for_image: bool = False, alt_name: str = None) -> str:
        """
        Zjednodušuje název produktu odstraněním nepotřebných slov a přívlastků.
        
        Args:
            product_name: Původní název produktu
            for_image: Pokud True, přeloží název do angličtiny pro generování obrázků
            alt_name: Alternativní název (pokud je poskytnut)
        """
        # Použití alternativního názvu, pokud je k dispozici
        if alt_name:
            product_name = alt_name

        # Kontrola prázdného nebo neplatného názvu
        if not product_name or not isinstance(product_name, str):
            return "unknown_product"

        # Seznam slov k odstranění
        remove_words = [
            'bio', 
            'selský', 
            'farmářský', 
            'domácí', 
            'tradiční', 
            'čerstvý',
            'přírodní', 
            'pravý', 
            'originální', 
            'extra', 
            'premium'
        ]

        # Převedení na malá písmena pro porovnání
        name_lower = product_name.lower()

        # Odstranění přívlastků
        for word in remove_words:
            name_lower = name_lower.replace(word.lower(), '').strip()

        # Odstranění velikosti/hmotnosti (např. "1 kg", "500g", "5 l")
        name_lower = re.sub(r'\s*\d+\s*[kgl][gl]?\b', '', name_lower)

        # Odstranění vícenásobných mezer
        simplified_name = ' '.join(name_lower.split())

        # Pokud je potřeba překlad pro generování obrázků
        if for_image:
            return self._translate_to_english(simplified_name)

        return simplified_name

    def _translate_to_english(self, text: str) -> str:
        """Překlad názvu do angličtiny s využitím cache."""
        cache_key = text.lower()
        
        # Kontrola cache
        if cache_key in self._translation_cache:
            return self._translation_cache[cache_key]
        
        try:
            prompt = f"""
            Přelož následující název produktu do angličtiny:
            {text}
            
            Pravidla pro překlad:
            1. Použij běžné anglické názvy pro potraviny
            2. Zachovej pouze základní název bez přívlastků
            3. Odpověz pouze překladem, nic jiného nepřidávej
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Jsi překladatel názvů potravin."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            translated_name = response.choices[0].message.content.strip()
            
            # Uložení do cache
            self._translation_cache[cache_key] = translated_name
            return translated_name
            
        except Exception as e:
            logger.error(f"Chyba při překladu: {str(e)}")
            return text 