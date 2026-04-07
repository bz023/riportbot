import pandas as pd
import os
import re

def get_excel_data(file_path):
    excel_to_web_id = {711: 5, 716: 10, 717: 9, 718: 31, 722: 12}
    tamogatott_markak = ["HAIER", "CANDY"]
    
    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, 'rb') as f:
            raw_content = f.read()
        
        text_content = raw_content.decode('latin-1', errors='ignore')
        lines = text_content.splitlines()

        extracted_data = []
        for line in lines:
            # Megnézzük, benne van-e valamelyik márka
            aktualis_marka = next((m for m in tamogatott_markak if m in line.upper()), None)
            if not aktualis_marka:
                continue

            # 1. Kategória kód (sor eleje)
            cat_match = re.search(r'(\d{3})', line[:10])
            if not cat_match: continue
            cat_kod = int(cat_match.group(1))

            # 2. MODELLNÉV JAVÍTÁSA: 
            # Keressük meg a márka pozícióját, és mindent utána a következő tabig (\t) modellnek veszünk
            try:
                # A sor elejétől a márkáig tartó részt levágjuk
                start_index = line.upper().find(aktualis_marka) + len(aktualis_marka)
                maradek_sor = line[start_index:].strip()
                
                # A maradékból csak az első tabulátorig tartó részt vesszük ki
                # Így a "27SB6-S" akkor is megmarad, ha van benne szóköz
                modellnev = maradek_sor.split('\t')[0].strip()
            except:
                modellnev = "ISMERETLEN"

            # 3. ÁR FIXÁLÁSA (marad a jól bevált tabos módszer)
            parts = line.strip().split('\t')
            ar = 0
            for p in reversed(parts):
                clean_p = re.sub(r'[^\d]', '', p.split(',')[0])
                if clean_p.isdigit():
                    val = int(clean_p)
                    # Mikrók miatt 5000-re levéve a limit
                    if 5000 < val < 2000000:
                        ar = val
                        break

            if cat_kod in excel_to_web_id and ar > 0:
                extracted_data.append({
                    'kategoria_kod': cat_kod,
                    'marka': aktualis_marka,
                    'modellnev': modellnev,
                    'ar': ar,
                    'raktar_hely': 6 if "\t6\t" in line else 5,
                    'web_id': excel_to_web_id[cat_kod]
                })

        return pd.DataFrame(extracted_data)
            
    except Exception as e:
        print(f"Hiba: {e}")
        return None