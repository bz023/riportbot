import os
import glob
import pandas as pd
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from reports import merch_report
from datetime import datetime
from data_loader import get_excel_data

load_dotenv()
mail = os.getenv("SPORTAL_MAIL")
passwd = os.getenv("SPORTAL_PASS")
store_name = os.getenv("STORE_NAME")
week = datetime.now().isocalendar()[1] 

def run_bot():
    downloads_dir = "/home/bz023/Downloads/"
    minden_xls = glob.glob(os.path.join(downloads_dir, "tblResult*.xls"))

    if not minden_xls:
        print("Nincs új feldolgozandó fájl.")
        return

    all_data_list = [get_excel_data(f) for f in minden_xls if get_excel_data(f) is not None]
    if not all_data_list: return
    
    final_data = pd.concat(all_data_list, ignore_index=True)
    final_data = final_data.sort_values(by=['modellnev', 'raktar_hely']).drop_duplicates(subset=['modellnev'])

    print(f"Összesítve {len(final_data)} termék feltöltése indul.")
    if input("Indítás? (1/q): ") != '1': return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        # --- ALERT KEZELÉS: Nem nyúlunk hozzá, hagyjuk a felhasználónak ---
        # Ha felugrik az ablak, csak kiírjuk, de nem fogadjuk el/utasítjuk el automatikusan
        page.on("dialog", lambda dialog: print(f"\n[ALERT ÉSZLELVE]: {dialog.message}\nKérlek, nyomj OK-t a böngészőben!"))

        try:
            # Login
            page.goto("https://salesportal.salesninja.hu/login")
            page.fill("input[name='email']", mail)
            page.fill("input[name='password']", passwd)
            page.click("button[type='submit']")
            page.wait_for_load_state("domcontentloaded")

            # Kitöltés hívása
            merch_report(page, store_name, week, final_data)

            print("\n" + "="*60)
            print("AUTOMATA KÉSZ. MOST TE JÖSSZ!")
            print("1. Kattints a beküldés/mentés gombra.")
            print("2. A felugró megerősítő ablakot te fogod látni, nyomj OK-t.")
            print("3. Ha végeztél, zárd be a böngészőt.")
            print("="*60)

            # Ez tartja nyitva a kapcsolatot a kattintásokhoz
            page.wait_for_event("close", timeout=0)

        except Exception as e:
            print(f"Hiba: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_bot()