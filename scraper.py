from playwright.sync_api import sync_playwright

def fetch_stores_and_weeks(email, password, selected_store=None, status_callback=None):
    stores = []
    weeks = []
    
    def report(text, progress_value):
        if status_callback:
            status_callback(text, progress_value)

    try:
        report("Böngésző indítása...", 0.1)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            report("Kapcsolódás a SalesPortal-hoz...", 0.2)
            page.goto("https://salesportal.salesninja.hu/login")
            
            report("Bejelentkezési adatok kitöltése...", 0.4)
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)
            page.click("button[type='submit']")
            page.wait_for_load_state("domcontentloaded")
            
            # Ellenőrizzük, hogy sikeres volt-e a belépés (pl. megjelent-e a hibaüzenet az oldalon)
            if page.locator(".alert-danger").is_visible() or "login" in page.url:
                browser.close()
                return [], []

            report("Riport oldal megnyitása...", 0.6)
            page.goto("https://salesportal.salesninja.hu/merchand-report")
            page.wait_for_selector("select[name='store']")
            
            if selected_store:
                report(f"'{selected_store}' heteinek ellenőrzése...", 0.8)
                page.select_option("select[name='store']", label=selected_store)
                page.wait_for_timeout(500)
                
                week_options = page.locator("select[name='week'] option:not([disabled])").all()
                weeks = [opt.get_attribute("value") for opt in week_options if opt.get_attribute("value")]
                
                report("Sikeres szinkronizáció!", 1.0)
                browser.close()
                return [], weeks
            
            report("Áruházak listájának letöltése...", 0.8)
            store_options = page.locator("select[name='store'] option").all()
            stores = [opt.inner_text().strip() for opt in store_options if opt.get_attribute("value")]
            
            report("Elérhető hetek letöltése...", 0.9)
            week_options = page.locator("select[name='week'] option").all()
            weeks = [opt.get_attribute("value") for opt in week_options if opt.get_attribute("value")]
            
            report("Sikeres szinkronizáció!", 1.0)
            browser.close()
    except Exception as e:
        print(f"Hiba a háttéradatok lekérése közben: {e}")
        raise e  # Továbbdobjuk a GUI-nak, hogy tudjon róla
        
    return stores, weeks