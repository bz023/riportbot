import os
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from reports import merch_report, weekly_report
from datetime import datetime

load_dotenv()
mail = os.getenv("SPORTAL_MAIL")
passwd = os.getenv("SPORTAL_PASS")
store_name = os.getenv("STORE_NAME")
curr_week = datetime.now().isocalendar()[1]
week = curr_week 

def run_bot():
    with sync_playwright() as p:
        # headless=False: látod mi történik, True: a háttérben fut
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("Sales Portal megnyitása...")
        page.goto("https://salesportal.salesninja.hu/login")

        # Bejelentkezés
        print("Bejelentkezés...")
        page.fill("input[name='email']", mail)
        page.fill("input[name='password']", passwd)
        page.click("button[type='submit']")

        page.wait_for_url("**/home")
        print("Sikeres bejelentkezés! /home megnyitva.")
        
        select_report_type(page)
        browser.close()


def select_report_type(page):
    print("--- Automata Riport Kitöltő ---")
    print("1. Merchandising riport feltöltése")
    print("2. Heti riport feltöltése")
    print("q. Kilépés")
    
    valasztas = input("\nMelyik folyamatot indítsam el? (1/2/q): ").strip().lower()

    if valasztas == '1':
        print("Indul a Merchand riport feltöltése...")
        merch_report(page, store_name, week)

    elif valasztas == '2':
        print("Indul a Heti riport feltöltése...")
        weekly_report(page, store_name, week)

    elif valasztas == 'q':
        print("Kilépés a programból.")
        exit()

    else:
        print("Hiba: Érvénytelen választás! Kérlek 1, 2 vagy q gombot nyomj.")
        return select_report_type(page)

if __name__ == "__main__":
    run_bot()