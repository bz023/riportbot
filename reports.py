import time

def fill_section(page, group, section_id, section_label):
    if group.empty:
        return

    print(f"   -> {section_label} kitöltése: {len(group)} db termék")
    
    for i, (idx, row) in enumerate(group.iterrows()):
        web_idx = i + 1
        prefix = f"{section_id}[{web_idx}]"

        if i > 0:
            # Plusz gomb
            page.locator(f"#{section_id} #plus").click()
            # Itt egy nagyon rövid sleep kell, mert a DOM-ban lehet, hogy már ott a mező, 
            # de a JS még nem kötötte rá az eseménykezelőket.
            time.sleep(0.2) 

        try:
            page.fill(f"input[name='{prefix}[product_name]']", str(row['modellnev']))
            page.select_option(f"select[name='{prefix}[brand_id]']", label=str(row['marka']).upper())
            page.select_option(f"select[name='{prefix}[subcategory_id]']", value=str(int(row['web_id'])))
            page.fill(f"input[name='{prefix}[product_price]']", str(row['ar']))

            if int(row['raktar_hely']) == 5:
                page.check(f"input[name='{prefix}[product_demo]'][value='Y']")
                page.check(f"input[name='{prefix}[product_clean]'][value='5']")
                page.select_option(f"select[name='{prefix}[product_placement]']", value="Sorban")
                page.check(f"input[name='{prefix}[product_pos]'][value='N']")
            else:
                page.check(f"input[name='{prefix}[product_demo]'][value='N']")

        except Exception as e:
            print(f"      Hiba a(z) {row['modellnev']} sornál: {e}")

def merch_report(page, store_name, week, data):
    print(f"Navigálás: https://salesportal.salesninja.hu/merchand-report")
    page.goto("https://salesportal.salesninja.hu/merchand-report")    

    # Üzlet kiválasztása
    page.wait_for_selector("select[name='store']")
    page.select_option("select[name='store']", label=store_name)
    
    # KIS SZÜNET: Az üzlet választása után az oldal gyakran újratölti a hetek listáját AJAX-szal
    time.sleep(1) 

    # Hét ellenőrzése
    page.wait_for_selector(f"select[name='week']")
    
    # Megnézzük, létezik-e az opció és tiltott-e
    option_selector = f"select[name='week'] option[value='{week}']"
    if page.locator(option_selector).count() == 0:
        print(f"HIBA: A(z) {week}. hét nem található a listában!")
        return

    is_disabled = page.eval_on_selector(option_selector, "el => el.disabled")
    if is_disabled:
        print(f"HIBA: A(z) {week}. hét le van tiltva!")
        return
    
    # Hét kiválasztása
    page.select_option("select[name='week']", value=str(week))
    
    # Itt kell egy stabil várás, mert a hétváltás után az egész táblázat újragenerálódik
    print(f"Hét ({week}) kiválasztva, várakozás a táblázatokra...")
    time.sleep(1.5)

    # Adatok szűrése
    refrigerators_data = data[data['web_id'].between(1, 8)]
    washers_dryers_data = data[data['web_id'].isin([9, 10, 11, 12, 13, 17, 18, 31])]
    microwaves_data = data[data['web_id'] == 19]
    built_in_data = data[data['web_id'].isin(list(range(20, 31)) + [32])]

    # Kitöltés
    if not refrigerators_data.empty: fill_section(page, refrigerators_data, "hutoszekrenyek", "Hűtők")
    if not washers_dryers_data.empty: fill_section(page, washers_dryers_data, "mosogepek", "Mosó/szárító/mosogatók")
    if not microwaves_data.empty: fill_section(page, microwaves_data, "sutok", "Mikrohullámú sütők")
    if not built_in_data.empty: fill_section(page, built_in_data, "beepitheto", "Beépíthető termékek")

    print("\nEllenőrzés...")
    page.click("button[name='test']")
    
    # A végén hagyjunk egy kis időt a szervernek
    time.sleep(1.5)
    if page.is_visible(".alert.alert-danger"):
        print(f"HIBA: {page.inner_text('.alert.alert-danger').strip()}")
    else:
        print("SIKER: Nincs hibaüzenet.")