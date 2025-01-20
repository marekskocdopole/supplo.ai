# Farm Product Manager

Aplikace pro správu produktů farem s automatickým generováním popisků pomocí AI.

## Lokální vývoj

### Požadavky
- Python 3.9+
- pip
- virtualenv

### Instalace
1. Naklonujte repozitář
```bash
git clone https://github.com/marekskocdopole/farm-product-manager.git
cd farm-product-manager
```

2. Vytvořte a aktivujte virtuální prostředí
```bash
python -m venv venv
source venv/bin/activate  # Pro Linux/Mac
# nebo
venv\Scripts\activate  # Pro Windows
```

3. Nainstalujte závislosti
```bash
pip install -r requirements.txt
```

4. Vytvořte .env soubor
```bash
cp .env.example .env
# Upravte proměnné v .env podle potřeby
```

### Spuštění
```bash
python run.py
```

Aplikace bude dostupná na http://localhost:5000

## Nasazení na Digital Ocean

1. Připojte se k serveru
```bash
ssh root@161.35.70.99
```

2. Naklonujte repozitář a nastavte prostředí
```bash
git clone https://github.com/marekskocdopole/farm-product-manager.git
cd farm-product-manager
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Nastavte produkční proměnné prostředí
```bash
nano .env
# Nastavte produkční hodnoty
```

4. Spusťte aplikaci pomocí Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:5000 "run:app"
```

## Struktura projektu

Detailní popis struktury projektu najdete v dokumentaci v `/docs`

## Testování

```bash
pytest
```

## Přispívání

1. Vytvořte fork
2. Vytvořte feature branch (`git checkout -b feature/AmazingFeature`)
3. Commitněte změny (`git commit -m 'Add some AmazingFeature'`)
4. Push do branch (`git push origin feature/AmazingFeature`)
5. Otevřete Pull Request 

# Supplo.ai

Aplikace pro generování popisků produktů pomocí AI.

Test automatického deploymentu po opravě SSH.

Test automatického deploymentu s novým SSH klíčem.

Test deploymentu po restartu serveru.

Deployment je nyní plně funkční a automatizovaný. 