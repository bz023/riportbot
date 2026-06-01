import os
import json
import time
import threading
import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, ttk  # TTK kell a táblázathoz (Treeview)
from datetime import datetime
from playwright.sync_api import sync_playwright
from cryptography.fernet import Fernet
from PIL import Image
from CTkMessagebox import CTkMessagebox
from reports import merch_report
from data_loader import get_excel_data

# GUI Megjelenés és téma beállítása
ctk.set_appearance_mode("Dark")  # Fix sötét mód a Haier logóhoz
ctk.set_default_color_theme("blue")

CONFIG_FILE = "config.enc"
KEY_FILE = "secret.key"

# --- 1. TITKOSÍTÁSI LOGIKA ---
def get_or_create_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as kf:
            kf.write(key)
        return key
    with open(KEY_FILE, "rb") as kf:
        return kf.read()

def save_credentials(email, password):
    key = get_or_create_key()
    fernet = Fernet(key)
    data = {"email": email, "password": password}
    encrypted_data = fernet.encrypt(json.dumps(data).encode())
    with open(CONFIG_FILE, "wb") as cf:
        cf.write(encrypted_data)

def load_credentials():
    if not os.path.exists(CONFIG_FILE) or not os.path.exists(KEY_FILE):
        return None
    try:
        key = get_or_create_key()
        fernet = Fernet(key)
        with open(CONFIG_FILE, "rb") as cf:
            encrypted_data = cf.read()
        decrypted_data = fernet.decrypt(encrypted_data).decode()
        return json.loads(decrypted_data)
    except Exception:
        return None

# --- 2. HÁTTÉR ADATLEKÉRÉS ---
def fetch_stores_and_weeks(email, password):
    stores = []
    weeks = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            page.goto("https://salesportal.salesninja.hu/login")
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)
            page.click("button[type='submit']")
            page.wait_for_load_state("domcontentloaded")
            
            page.goto("https://salesportal.salesninja.hu/merchand-report")
            page.wait_for_selector("select[name='store']")
            
            store_options = page.locator("select[name='store'] option").all()
            stores = [opt.inner_text().strip() for opt in store_options if opt.get_attribute("value")]
            
            week_options = page.locator("select[name='week'] option").all()
            weeks = [opt.get_attribute("value") for opt in week_options if opt.get_attribute("value")]
            
            browser.close()
    except Exception as e:
        print(f"Hiba a háttéradatok lekérése közben: {e}")
    return stores, weeks

# --- 3. GRAFIKUS FELÜLET (GUI) ---
class SalesBotGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SalesPortal Merch Bot v2.0")
        self.geometry("800x850")  # Beállítva a kért új ablakméret
        self.resizable(False, False)
        
        # Golyóálló kilépés az X gombra
        self.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
        
        self.selected_files = []
        self.final_dataframe = None  # Itt tároljuk a beolvasott tiszta adatokat
        self.credentials = load_credentials()

        if not self.credentials:
            self.build_login_ui()
        else:
            threading.Thread(target=self.preload_data, daemon=True).start()

    def build_login_ui(self):
        self.clear_ui()
        
        title = ctk.CTkLabel(self, text="Első indítás: Bejelentkezés", font=ctk.CTkFont(family="Arial", size=18, weight="bold"))
        title.pack(pady=20)

        self.email_entry = ctk.CTkEntry(self, placeholder_text="Email cím", width=300)
        self.email_entry.pack(pady=10)

        self.pass_entry = ctk.CTkEntry(self, placeholder_text="Jelszó", show="*", width=300)
        self.pass_entry.pack(pady=10)

        self.login_btn = ctk.CTkButton(self, text="Mentés és kapcsolódás", fg_color="#005baa", hover_color="#00437d", command=self.handle_login)
        self.login_btn.pack(pady=20)
        
        self.status_label = ctk.CTkLabel(self, text="", text_color="red")
        self.status_label.pack(pady=5)

    def handle_login(self):
        email = self.email_entry.get().strip()
        password = self.pass_entry.get().strip()
        
        if not email or not password:
            self.status_label.configure(text="Minden mezőt ki kell tölteni!")
            return
        
        self.status_label.configure(text="Ellenőrzés és adatok lekérése...", text_color="orange")
        self.update()
        
        stores, weeks = fetch_stores_and_weeks(email, password)
        
        if stores:
            save_credentials(email, password)
            self.credentials = {"email": email, "password": password}
            self.build_main_ui(stores, weeks)
        else:
            self.status_label.configure(text="Sikertelen belépés! Ellenőrizd az adatokat.", text_color="red")

    def preload_data(self):
        self.clear_ui()
        loading_label = ctk.CTkLabel(self, text="Kapcsolódás a SalesPortal-hoz...\n\nÁruházak és hetek letöltése folyamatban.", font=ctk.CTkFont(family="Arial", size=14))
        loading_label.pack(pady=(250, 20))
        
        self.progress_bar = ctk.CTkProgressBar(self, width=300)
        self.progress_bar.pack(pady=10)
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        self.update()
        
        stores, weeks = fetch_stores_and_weeks(self.credentials["email"], self.credentials["password"])
        self.progress_bar.stop()
        
        if stores:
            self.after(0, lambda: self.build_main_ui(stores, weeks))
        else:
            self.after(0, self.build_login_ui)

    def build_main_ui(self, stores, weeks):
        self.clear_ui()
        
        # --- 1. LOGO MEGJELENÍTÉSE ---
        logo_path = "haier.png"
        if os.path.exists(logo_path):
            raw_img = Image.open(logo_path)
            logo_img = ctk.CTkImage(light_image=raw_img, dark_image=raw_img, size=(300, 93))
            logo_label = ctk.CTkLabel(self, text="", image=logo_img)
            logo_label.pack(pady=(20, 5))

        ctk.CTkLabel(self, text="SalesNinja Merchandising Riport", font=ctk.CTkFont(family="Arial", size=16, weight="bold")).pack(pady=(0, 15))

        # --- 2. INPUT MEZŐK ---
        ctk.CTkLabel(self, text="Áruház kiválasztása:", font=ctk.CTkFont(size=12)).pack(pady=2)
        self.store_combo = ctk.CTkComboBox(self, values=stores, width=400, state="readonly")
        self.store_combo.pack(pady=5)
        
        env_store = os.getenv("STORE_NAME")
        if env_store in stores:
            self.store_combo.set(env_store)

        ctk.CTkLabel(self, text="Riport hete:", font=ctk.CTkFont(size=12)).pack(pady=2)
        current_iso_week = str(datetime.now().isocalendar()[1])
        self.week_combo = ctk.CTkComboBox(self, values=weeks, width=400, state="readonly")
        self.week_combo.pack(pady=5)
        if current_iso_week in weeks:
            self.week_combo.set(current_iso_week)

        # --- 3. TALLÓZÁS ---
        self.btn_browse = ctk.CTkButton(
            self, 
            text="WAWI-s Excel fájlok kiválasztása", 
            width=250, 
            height=35,
            fg_color="#005baa", 
            hover_color="#00437d",
            font=ctk.CTkFont(family="Arial", size=13, weight="bold"),
            command=self.browse_files
        )
        self.btn_browse.pack(pady=15)

        self.file_status_label = ctk.CTkLabel(self, text="Nincs fájl kiválasztva.", text_color="#005baa", font=ctk.CTkFont(weight="bold"))
        self.file_status_label.pack(pady=(0, 10))

        # ================
        # --- ELŐNÉZET ---
        # ================
        
        custom_bg_pair = ["#EAEAEA", "#1A1A1A"] 
        
        bg_color = self._apply_appearance_mode(custom_bg_pair)
        text_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        accent_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        selected_text = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["text_color"])
        header_bg = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])

        style = ttk.Style()
        style.theme_use("clam")
        
        # Tisztítjuk a layoutot
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
        style.layout("Treeview.Heading", [
            ('Treeview.heading.cell', {'sticky': 'nswe', 'children': [
                ('Treeview.heading.border', {'sticky': 'nswe', 'children': [
                    ('Treeview.heading.padding', {'sticky': 'nswe', 'children': [
                        ('Treeview.heading.image', {'side': 'right', 'sticky': ''}),
                        ('Treeview.heading.text', {'sticky': ''})
                    ]})
                ]})
            ]})
        ])

        # Táblázat törzs
        style.configure(
            "Treeview", 
            background=bg_color, 
            foreground=text_color, 
            fieldbackground=bg_color, 
            rowheight=25,
            borderwidth=0,
            highlightthickness=0,
            relief="flat"
        )
        
        # Fejléc a fehér elválasztó vonallal
        style.configure(
            "Treeview.Heading", 
            background=header_bg, 
            foreground=text_color, 
            font=("Arial", 11, "bold"),
            borderwidth=1,
            relief="flat",
            lightcolor="white",
            darkcolor="white"
        )
        
        style.map("Treeview", background=[('selected', accent_color)], foreground=[('selected', selected_text)])

        # Közvetlenül a 'self'-re tesszük, height=5 kényszeríti a fix méretet
        self.tree = ttk.Treeview(
            self, 
            columns=("Modell", "Raktárhely", "Mennyiség"), 
            show="headings", 
            height=5, 
            style="Treeview"
        )
        
        self.tree.configure(takefocus=False)
        
        # Igazítások a korábbi tökéletes verzió szerint
        self.tree.heading("Modell", text="Modell név", anchor="w")
        self.tree.heading("Raktárhely", text="Kiállított?", anchor="center")
        self.tree.heading("Mennyiség", text="Készlet (db)", anchor="center")
        
        self.tree.column("Modell", width=350, anchor="w")
        self.tree.column("Raktárhely", width=180, anchor="center")
        self.tree.column("Mennyiség", width=120, anchor="center")
        
        # Elhelyezés szép tágas térközzel
        self.tree.pack(pady=25, padx=50)
        # --- 5. INDÍTÁS GOMB ---
        self.btn_run = ctk.CTkButton(
            self, 
            text="ROBOT INDÍTÁSA", 
            width=250, 
            height=40, 
            font=ctk.CTkFont(family="Arial", size=14, weight="bold"), 
            fg_color="green", 
            hover_color="darkgreen", 
            command=self.run_bot_logic
        )
        self.btn_run.pack(pady=25)

        # --- 6. KIJELENTKEZÉS GOMB ---
        btn_logout = ctk.CTkButton(
            self, 
            text="Bejelentkezési adatok törlése", 
            width=180, 
            height=25, 
            fg_color="maroon", 
            hover_color="red", 
            command=self.logout
        )
        btn_logout.pack(side="bottom", pady=15)
        # =====================================================================

    def browse_files(self):
        files = filedialog.askopenfilenames(title="Válaszd ki a WAWI fájlokat", filetypes=[("Excel fájlok", "*.xls *.xlsx")])
        if files:
            self.selected_files = list(files)
            self.file_status_label.configure(text=f"{len(self.selected_files)} db fájl sikeresen betöltve.", text_color="green")
            
            # Adatok azonnali feldolgozása az előnézethez
            all_data_list = [get_excel_data(f) for f in self.selected_files if get_excel_data(f) is not None]
            if all_data_list:
                self.final_dataframe = pd.concat(all_data_list, ignore_index=True)
                self.final_dataframe = self.final_dataframe.sort_values(by=['modellnev', 'raktar_hely'], ascending=[True, True])
                self.final_dataframe = self.final_dataframe.drop_duplicates(subset=['modellnev'], keep='first')
                
                # Táblázat frissítése a képernyőn
                self.update_table_preview()
            else:
                CTkMessagebox(title="Hiba", message="A kijelölt fájlokból nem lehetett adatot kiolvasni!", icon="cancel")

    def update_table_preview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        top_5_data = self.final_dataframe.head(5)
            
        for _, row in top_5_data.iterrows():
            model = row.get('modellnev', 'Ismeretlen')
            qty = row.get('db', row.get('keszlet', 1)) 
            
            # Raktárhely fordítása
            raw_loc = row.get('raktar_hely', '-')
            loc_str = str(raw_loc).strip()
            
            if loc_str == "5":
                loc = "Igen"
            elif loc_str == "6":
                loc = "Nem"
            else:
                loc = f"Egyéb ({loc_str})" if loc_str and loc_str != "-" else "-"
            
            self.tree.insert("", "end", values=(model, loc, qty))
            
        self.tree.selection_remove(self.tree.selection())

    def run_bot_logic(self):
        if self.final_dataframe is None or self.final_dataframe.empty:
            CTkMessagebox(title="Figyelem", message="Előbb válassz ki érvényes WAWI fájlokat!", icon="warning")
            return

        store = self.store_combo.get()
        week = self.week_combo.get()

        self.btn_run.configure(state="disabled", text="ROBOT FUT...")

        # Háttérszál indítása
        bot_thread = threading.Thread(target=self.execute_playwright, args=(store, week, self.final_dataframe))
        bot_thread.daemon = True
        bot_thread.start()

    def execute_playwright(self, store, week, final_data):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, args=["--start-maximized"])
            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            
            page.on("dialog", lambda dialog: print(f"\n[ALERT]: {dialog.message}\nNyomj OK-t!"))

            try:
                page.goto("https://salesportal.salesninja.hu/login")
                page.fill("input[name='email']", self.credentials["email"])
                page.fill("input[name='password']", self.credentials["password"])
                page.click("button[type='submit']")
                page.wait_for_load_state("domcontentloaded")

                # Riport futtatása
                merch_report(page, store, week, final_data)

                print("\n" + "="*50)
                print("AUTOMATIZÁCIÓ KÉSZ. VEDD ÁT AZ IRÁNYÍTÁST!")
                print("="*50)

                page.wait_for_event("close", timeout=0)
            except Exception as e:
                print(f"Hiba futás közben: {e}")
            finally:
                browser.close()
        
        self.after(0, lambda: self.btn_run.configure(state="normal", text="ROBOT INDÍTÁSA"))

    def logout(self):
        if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)
        if os.path.exists(KEY_FILE): os.remove(KEY_FILE)
        self.credentials = None
        self.build_login_ui()

    def clear_ui(self):
        for widget in self.winfo_children():
            widget.pack_forget()

if __name__ == "__main__":
    app = SalesBotGUI()
    app.mainloop()