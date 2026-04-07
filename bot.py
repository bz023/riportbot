import os
import glob
import pandas as pd
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from reports import merch_report
from datetime import datetime
from data_loader import get_excel_data

# Beállítások betöltése
load_dotenv()
mail = os.getenv("SPORTAL_MAIL")
passwd = os.getenv("SPORTAL_PASS")
store_name = os.getenv("STORE_NAME")
week = datetime.now().isocalendar()[1] 

def run_bot():
    downloads_dir = "/home/bz023/Downloads/"
    
    minden_xls = glob.glob(os.path.join(downloads_dir, "tblResult*.xls"))
    fajlok = [f for f in minden_xls]

    if not fajlok:
        print("Nincs új feldolgozandó tblResult fájl.")
        return

    # 2. Adatok összesítése az összes talált fájlból
    all_data_list = []
    feldolgozott_fajlok = []

    for f_path in fajlok:
        df = get_excel_data(f_path)
        if df is not None and not df.empty:
            all_data_list.append(df)
            feldolgozott_fajlok.append(f_path)

    if not all_data_list:
        print("Nem sikerült érvényes adatot kinyerni a fájlokból.")
        return

    final_data = pd.concat(all_data_list, ignore_index=True)

    # 3. DUPLIKÁCIÓ SZŰRÉSE (5-ös kód (kiállított) előnyben)
    # Raktar_hely szerint rendezünk (5 elöl, 6 hátul), majd kidobjuk a modellnév duplikációkat
    final_data = final_data.sort_values(by=['modellnev', 'raktar_hely'], ascending=[True, True])
    final_data = final_data.drop_duplicates(subset=['modellnev'], keep='first')

    print(f"Összesítve {len(final_data)} egyedi termék feltöltése indul.")

    # 4. Feltöltési folyamat kiválasztása
    print("\n1. Merchandising riport")
    valasztas = input("Választás (1 vagy q): ").strip().lower()
    if valasztas != '1': return

    # 5. Playwright vezérlés
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        try:
            # Login
            page.goto("https://salesportal.salesninja.hu/login")
            page.fill("input[name='email']", mail)
            page.fill("input[name='password']", passwd)
            page.click("button[type='submit']")
            page.wait_for_url("**/home")
            print("Sikeres login!")

            # Feltöltés indítása (az összesített adatokkal)
            merch_report(page, store_name, week, final_data)

            print("\n>>> KÉSZ! Minden fájl feldolgozva és feltöltve.")

        except Exception as e:
            print(f"Hiba a feltöltés során: {e}")
        
        finally:
            input("\nNyomj Enter-t a böngésző bezárásához...")
            browser.close()

if __name__ == "__main__":
    run_bot()