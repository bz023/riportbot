import time

def fill_section(page, group, section_id, section_label):
    if group.empty:
        return

    print(f"   -> {section_label} kitöltése: {len(group)} db termék")
    
    for i, (idx, row) in enumerate(group.iterrows()):
        # 1. Sor hozzáadása (ha nem az első termék)
        if i > 0:
            # A szekción belüli plusz gomb megnyomása
            page.locator(f"#{section_id}").locator("#plus").click()
            time.sleep(0.5) 

        web_idx = i + 1
        prefix = f"{section_id}[{web_idx}]"

        try:
            # Modellnév
            page.fill(f"input[name='{prefix}[product_name]']", str(row['modellnev']))
            
            # Márka kiválasztása (az Excel 'marka' oszlopa alapján, label-lel)
            page.select_option(f"select[name='{prefix}[brand_id]']", label=str(row['marka']).upper())
            
            # Kategória kiválasztása (web_id alapján)
            page.select_option(f"select[name='{prefix}[subcategory_id]']", value=str(int(row['web_id'])))
            
            page.fill(f"input[name='{prefix}[product_price]']", str(row['ar']))

            is_kiallitott = (int(row['raktar_hely']) == 5)

            if is_kiallitott:
                # KIÁLLÍTOTT ESETÉN (5-ös kód)
                page.check(f"input[name='{prefix}[product_demo]'][value='Y']") # Kiállított: Igen
                page.check(f"input[name='{prefix}[product_clean]'][value='5']") # Tisztaság: 5
                page.select_option(f"select[name='{prefix}[product_placement]']", value="Sorban") # Elhelyezés: Sorban
                page.check(f"input[name='{prefix}[product_pos]'][value='N']") # POS: Nem
            else:
                # RAKTÁRI ESETÉN (Minden más kód)
                page.check(f"input[name='{prefix}[product_demo]'][value='N']") # Kiállított: Nem
                # A többi mező alapértéken

        except Exception as e:
            print(f"      Hiba a(z) {row['modellnev']} sornál: {e}")


def merch_report(page, store_name, week, data):

    print(f"Navigálás a Merchandising riport oldalra (üzlet: {store_name})...")
    page.goto("https://salesportal.salesninja.hu/merchand-report")    
    print("...oldal betöltve")

    page.wait_for_selector("select[name='store']")
    page.select_option("select[name='store']", label=store_name)
    print(f"{store_name} üzlet kiválasztva")

    page.wait_for_selector("select[name='week']")
    is_disabled = page.eval_on_selector(
        f"select[name='week'] option[value='{week}']", 
        "el => el.disabled"
    )

    if is_disabled:
        print(f"HIBA: A(z) {week}. hét le van tiltva (disabled) ezen az oldalon!")
        return
    
    page.select_option("select[name='week']", value=str(week))
    print(f"Hét ({week}) sikeresen kiválasztva.")

    page.wait_for_load_state("networkidle")
    time.sleep(0.5)

    # Hűtők (Web ID: 1-8)
    refrigerators_data = data[data['web_id'].between(1, 8)]
    
    # Mosó/szárító/mosogató (9, 10, 11, 12, 13, 17, 18, 31)
    washers_dryers_data = data[data['web_id'].isin([9, 10, 11, 12, 13, 17, 18, 31])]
    
    # Mikró (19)
    microwaves_data = data[data['web_id'] == 19]
    
    # Beépíthetők (20-30 + 32)
    built_in_ids = list(range(20, 31)) + [32]
    built_in_data = data[data['web_id'].isin(built_in_ids)]

    if not refrigerators_data.empty:
        print(f"-> Hűtőszekrények kitöltése ({len(refrigerators_data)} db)...")
        fill_section(page, refrigerators_data, "hutoszekrenyek", "Hűtők")

    if not washers_dryers_data.empty:
        print(f"-> Mosó/szárító/mosogató kitöltése ({len(washers_dryers_data)} db)...")
        fill_section(page, washers_dryers_data, "mosogepek", "Mosó/szárító/mosogatók")

    if not microwaves_data.empty:
        print(f"-> Mikrohullámú sütők kitöltése ({len(microwaves_data)} db)...")
        fill_section(page, microwaves_data, "sutok", "Mikrohullámú sütők")

    if not built_in_data.empty:
        print(f"-> Beépíthető készülékek kitöltése ({len(built_in_data)} db)...")
        fill_section(page, built_in_data, "beepitheto", "Beépíthető termékek")

    
    print("\nAdatkitöltés kész. Ellenőrzés indítása a 'Riport tartalom tesztelése' gombbal...")
    
    page.click("button[name='test']")
    
    time.sleep(2)
    
    hiba_lathato = page.is_visible(".alert.alert-danger")

    if hiba_lathato:
        alert_text = page.inner_text(".alert.alert-danger").strip()
        print(f"\nHIBA: A portál hibát jelzett!")
        print(f"Üzenet: {alert_text}")
    else:
        print("\nSIKER: Nem érkezett hibaüzenet, a tartalom valószínűleg rendben van.")

def weekly_report(page, store_name, week):
    print("NOT IMPLEMENTED")
    #page.goto("https://salesportal.salesninja.hu/weekly-report-v3")
    
    #TODO...


    #print("Heti riport oldal kész.")
    time.sleep(1)