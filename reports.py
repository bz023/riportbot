import time

def fill_section(page, group, section_id, section_label):
    if group.empty:
        return

    print(f"   -> {section_label} kitöltése: {len(group)} db termék")
    
    for i, (idx, row) in enumerate(group.iterrows()):
        web_idx = i + 1
        prefix = f"{section_id}[{web_idx}]"

        if i > 0:
            page.locator(f"#{section_id} #plus").click()
            time.sleep(0.3) 

        try:
            # MODELLNÉV: Kattintás, törlés, gépelés + események
            name_sel = f"input[name='{prefix}[product_name]']"
            page.locator(name_sel).click()
            page.locator(name_sel).fill("")
            page.locator(name_sel).press_sequentially(str(row['modellnev']), delay=15)
            page.locator(name_sel).dispatch_event("change")
            page.locator(name_sel).dispatch_event("blur")

            # MÁRKA ÉS KATEGÓRIA
            page.select_option(f"select[name='{prefix}[brand_id]']", label=str(row['marka']).upper())
            page.select_option(f"select[name='{prefix}[subcategory_id]']", value=str(int(row['web_id'])))
            
            # ÁR: Kattintás, gépelés + események
            price_sel = f"input[name='{prefix}[product_price]']"
            page.locator(price_sel).click()
            page.locator(price_sel).fill("")
            page.locator(price_sel).press_sequentially(str(row['ar']), delay=15)
            page.locator(price_sel).dispatch_event("change")

            # Raktárhely logika
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
    print(f"Navigálás a riport oldalra...")
    page.goto("https://salesportal.salesninja.hu/merchand-report")    

    page.wait_for_selector("select[name='store']")
    page.select_option("select[name='store']", label=store_name)
    time.sleep(1) 

    page.select_option("select[name='week']", value=str(week))
    time.sleep(1) 

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

    # Egy utolsó kattintás a semmibe, hogy minden mező validálódjon
    page.mouse.click(0, 0)
    print("\nAdatkitöltés kész!")