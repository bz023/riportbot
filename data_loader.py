import pandas as pd
import os
import re

def get_excel_data(file_path):
    excel_to_web_id = {
        710:1,  # Tabletop 85cm
        740:2,  # Egyajtós álló hűtő
        742:3,  # Double door felülfagyasztó
        710:4,  # Nem nofrost
        711:5,  # Nofrost
        713:6,  # Fagyasztó 85cm-ig    
        745:7,  # Fagyasztó 85cm felett
        714:8,   # Fagyláda
        717:9,    # Elöltöltős 60 
        716:10,   # Elöltöltős 45
        715:11,   # Felültöltős
        722:12,   # Hőszivattyús
        #1:13,  #Kondenzációs   
        #1:14, #14 gáztűzhely, 15 kombi, 16 elektromos
        #1:15,
        #1:16,
        724:17,   #45cm mosogató
        723:18,   #60cm mosogató
        #1:19,   #Mikró
        #1:20,   #Beép sütő
        781:21,   # Indukciós lap
        771:22,   # Kerámialap
        #1:23,   # Gáz főzőlap
        793:24,   # Beép mikró
        823:25,   # Páraelszívó
        737:26,   # Beép 45cm mosogató
        794:27,   # Beép 60cm mosogató
        778:28,   # Beép hűtő
        #1:29,   # Pároló
        #1:30,   # Kávéfőző
        718:31, # Mosószárító
        #1:32    # Beép mosógép
        }
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