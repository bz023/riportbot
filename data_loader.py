import pandas as pd
import os

def get_excel_data(file_path):
    # 1. Ez az Árucsoport kódokat fordítja le a weboldal által használt ID-kra
    excel_to_web_id = {
        716: 10,  # Árucsoport 716 -> Web 10
        717: 9,   # Árucsoport 717 -> Web 9
        711: 5,
        # ... TODO ...
    }

    web_id_to_label = {
        1: "Table top (0-85 cm-ig)", 2: "Cabinet (egyajtós)", 3: "Double Door (felülfagyasztós, 2 ajtós)",
        4: "Alulfagyasztós (nem No-Frost)", 5: "Alulfagyasztós (No-Frost)", 6: "Freezer Upright below 85 cm (85 cm-ig)",
        7: "Freezer Upright above 85 cm (85 cm felett)", 8: "Freezer Horizontal (fagyasztóláda)",
        9: "Frontloader 60 cm (elöltöltős)", 10: "Frontloader 45 cm (keskeny elöltöltős)",
        11: "Toploader (felültöltős)", 12: "Heatpump Dryer (hőszivattyús)", 13: "Condenser (kondenzációs)",
        14: "Gas hobs (tűzhely - gáz)", 15: "Combi hobs/ovens (tűzhely - gáz/villany)", 16: "Electric hobs (elektromos)",
        17: "Dishwasher 45 cm", 18: "Dishwasher 60 cm", 19: "Microwaves (mikrohullámú sütők)", 20: "Ovens (sütő)",
        21: "Induction hobs (indukciós főzőlap)", 22: "Normal hobs (kerámia főzőlap)", 23: "Gas hobs (gáz főzőlap)",
        24: "Microwaves (mikrohullámú sütő)", 25: "Hoods (páraelszívó)", 26: "Dishwashers 45 cm (mosogatógép 45 cm)",
        27: "Dishwashers 60 cm (mosogatógép 60 cm)", 28: "Refrigerators (hűtőszekrény)", 29: "Steamers (pároló)",
        30: "Coffee makers (kávéfőző)", 31: "Combination washers (mosó-szárító)", 32: "Washers (mosógép)"
    }

    if not os.path.exists(file_path):
        print(f"HIBA: A fájl nem található: {file_path}")
        return None

    try:
        df = pd.read_excel(file_path, header=None)
        df.columns = ['modellnev', 'marka', 'kategoria_kod', 'raktar_hely', 'ar']

        # Árucsoport => selector ID
        df['web_id'] = df['kategoria_kod'].map(excel_to_web_id)

        # Selector ID => Selector label
        df['kategoria_nev'] = df['web_id'].map(web_id_to_label)
        
        # Ha valami hiányzik a szótárból, jelezzük
        if df['kategoria_nev'].isnull().any():
            missing = df[df['kategoria_nev'].isnull()]['kategoria_kod'].unique()
            print(f"FIGYELEM: Nincs fordítás ezekhez az Árucsoport kódokhoz: {missing}")

        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)

        print(f"Sikeres beolvasás: {len(df)} termék betöltve.")
        return df

    except Exception as e:
        print(f"Hiba: {e}")
        return None
    
    # --- TESZT FUNKCIÓ (MAIN) ---
if __name__ == "__main__":
    print(">>> Tesztelés indítása...")
    
    filename = "termekek.xlsx"
    data = get_excel_data(filename)

    if data is not None:
        print(f"\n>>> SIKERES BEOLVASÁS!")
        print(data.head())