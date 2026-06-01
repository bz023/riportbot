import os
import glob
import pandas as pd
import time
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

def run_bot():
    # 1. HÉT BEKÉRÉSE (Alapértelmezett a jelenlegi hét)
    current_iso_week = datetime.now().isocalendar()[1]
    print(f"\n" + "="*40)
    print(f" JELENLEGI HÉT: {current_iso_week}")
    print("="*40)
    
    user_input_week = input(f"Melyik hétre töltsünk? [Üres = {current_iso_week}, kilépés = q]: ").strip()
    
    if user_input_week.lower() == 'q':
        print("Kilépés...")
        return
    
    # Ha üres az input, a jelenlegi hetet használja, egyébként amit beírtál
    try:
        target_week = int(user_input_week) if user_input_week else current_iso_week
    except ValueError:
        print("HIBA: Érvénytelen hétformátum! Kérlek számot adj meg.")
        return

    # 2. ADATOK BETÖLTÉSE ÉS ÖSSZESÍTÉSE
    downloads_dir = "/home/bz023/Downloads/"
    minden_xls = glob.glob(os.path.join(downloads_dir, "tblResult*.xls"))

    if not minden_xls:
        print(f"Nincs új feldolgozandó tblResult fájl a {downloads_dir} mappában.")
        return

    print(f"Fájlok beolvasása és összefésülése...")
    all_data_list = []
    for f_path in minden_xls:
        df = get_excel_data(f_path)
        if df is not None and not df.empty:
            all_data_list.append(df)

    if not all_data_list:
        print("Nem sikerült érvényes adatot kinyerni a fájlokból.")
        return

    final_data = pd.concat(all_data_list, ignore_index=True)

    # Duplikáció szűrése (modellnév alapján, kiállított (5-ös) előnyben)
    final_data = final_data.sort_values(by=['modellnev', 'raktar_hely'], ascending=[True, True])
    final_data = final_data.drop_duplicates(subset=['modellnev'], keep='first')

    print(f"KÉSZ: {len(final_data)} egyedi termék készen áll a feltöltésre.")
    
    valasztas = input(f"\nIndíthatom a feltöltést a {target_week}. hétre? (1 = Igen / q = Nem): ").strip().lower()
    if valasztas != '1':
        return

    # 3. PLAYWRIGHT FOLYAMAT
    with sync_playwright() as p:
        # Fullscreen indítás
        browser = p.chromium.launch(
            headless=False, 
            args=["--start-maximized"]
        )
        
        # no_viewport=True, hogy ne legyen fekete keret
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        # MEGERŐSÍTŐ ABLAK (ALERT/CONFIRM) KEZELÉSE
        # Ez biztosítja, hogy a Playwright ne zárja be automatikusan a felugró ablakot
        page.on("dialog", lambda dialog: print(f"\n[FELUGRÓ ABLAK ÉSZLELVE]: {dialog.message}\nKérlek, nyomj OK-t a böngészőben!"))

        try:
            # Login
            print("\nBelépés a SalesPortal-ra...")
            page.goto("https://salesportal.salesninja.hu/login")
            page.fill("input[name='email']", mail)
            page.fill("input[name='password']", passwd)
            page.click("button[type='submit']")
            
            # Megvárjuk a sikeres belépést
            page.wait_for_load_state("domcontentloaded")
            print("Sikeres login!")

            # Feltöltés indítása (átadjuk a kiválasztott hetet)
            merch_report(page, store_name, target_week, final_data)

            print("\n" + "!"*50)
            print(f" AZ AUTOMATA KITÖLTÉS A {target_week}. HÉTRE BEFEJEZŐDÖTT!")
            print(" 1. Ellenőrizd az adatokat a böngészőben.")
            print(" 2. Kattints a beküldés gombra.")
            print(" 3. A felugró megerősítést te fogod látni, OK-zd le.")
            print(" 4. Ha végeztél, zárd be a böngészőablakot.")
            print("!"*50)

            # Ez a sor tartja életben a böngészőt, amíg manuálisan be nem zárod
            page.wait_for_event("close", timeout=0)

        except Exception as e:
            print(f"\nHIBA történt a folyamat során: {e}")
        
        finally:
            print("Script leállítása...")
            browser.close()

if __name__ == "__main__":
    run_bot()