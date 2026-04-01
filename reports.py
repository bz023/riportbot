import time

def merch_report(page):
    print("Navigálás a Merchandising riport oldalra...")
    page.goto("https://salesportal.salesninja.hu/merchand-report")
    
    #TODO

    print("Merchandising riport oldal kész.")
    time.sleep(5)

def weekly_report(page):
    print("Navigálás a Heti riport oldalra...")
    page.goto("https://salesportal.salesninja.hu/weekly-report-v3")
    
    #TODO...

    
    print("Heti riport oldal kész.")
    time.sleep(5)