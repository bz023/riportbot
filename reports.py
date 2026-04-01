import time

def merch_report(page, store_name, week):

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
    time.sleep(5)

def weekly_report(page, store_name, week):
    print("Navigálás a Heti riport oldalra...")
    page.goto("https://salesportal.salesninja.hu/weekly-report-v3")
    
    #TODO...


    print("Heti riport oldal kész.")
    time.sleep(5)