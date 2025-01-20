import re

class ProductNameProcessor:
    def __init__(self):
        self._translation_cache = {}  # Cache pro překlady
        self._product_type_cache = {} # Cache pro typy produktů

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
            "bio", 
            "selský", 
            "farmářský", 
            "domácí", 
            "tradiční", 
            "čerstvý",
            "přírodní", 
            "pravý", 
            "originální", 
            "extra", 
            "premium"
        ]

        # Převedení na malá písmena pro porovnání
        name_lower = product_name.lower()

        # Odstranění přívlastků
        for word in remove_words:
            name_lower = name_lower.replace(word.lower(), "").strip()

        # Odstranění velikosti/hmotnosti (např. "1 kg", "500g", "5 l")
        name_lower = re.sub(r"\s*\d+\s*[kgl][gl]?\b", "", name_lower)

        # Odstranění vícenásobných mezer
        simplified_name = " ".join(name_lower.split())

        return simplified_name

    def validate_product_name(self, name: str) -> bool:
        """Validace názvu produktu."""
        if not name:
            return False
            
        # Minimální délka
        if len(name.strip()) < 3:
            return False
            
        # Maximální délka
        if len(name) > 100:
            return False
            
        # Povolené znaky
        if not re.match(r"^[\w\s\-áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]+$", name):
            return False
            
        return True 