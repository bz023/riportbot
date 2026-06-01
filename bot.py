import PIL._tkinter_finder
import os
import threading
import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, ttk
from datetime import datetime
from PIL import Image
from CTkMessagebox import CTkMessagebox

# SAJÁT MODULOK
import auth
from scraper import fetch_stores_and_weeks
from reports import merch_report
from data_loader import get_excel_data
from gui_styles import get_asset_path, apply_treeview_style

class SalesBotGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SalesPortal Merch Bot v2.0")
        self.geometry("800x900")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
        
        self.selected_files = []
        self.final_dataframe = None
        self.credentials = auth.load_credentials()

        if not self.credentials:
            self.build_login_ui()
        else:
            threading.Thread(target=self.preload_data, daemon=True).start()

    def build_login_ui(self):
        self.clear_ui()
        logo_path = get_asset_path(os.path.join("assets", "haier.png"))
        if os.path.exists(logo_path):
            raw_img = Image.open(logo_path)
            logo_img = ctk.CTkImage(light_image=raw_img, dark_image=raw_img, size=(260, 80))
            ctk.CTkLabel(self, text="", image=logo_img).pack(pady=(60, 10))
        
        ctk.CTkLabel(self, text="SalesPortal Merch Bot | Bejelentkezés", font=ctk.CTkFont(family="Arial", size=15, weight="bold")).pack(pady=(0, 20))
        
        email_label = ctk.CTkLabel(self, text="E-mail cím", font=ctk.CTkFont(family="Arial", size=11, weight="bold"), text_color="gray", anchor="w")
        email_label.pack(padx=240, fill="x", pady=(5, 2))
        
        self.email_entry = ctk.CTkEntry(self, placeholder_text="E-mail", width=320, height=35)
        self.email_entry.pack(pady=(0, 10))
        
        pass_label = ctk.CTkLabel(self, text="SalesPortal Jelszó", font=ctk.CTkFont(family="Arial", size=11, weight="bold"), text_color="gray", anchor="w")
        pass_label.pack(padx=240, fill="x", pady=(5, 2))
        
        self.pass_entry = ctk.CTkEntry(self, placeholder_text="Jelszó", show="*", width=320, height=35)
        self.pass_entry.pack(pady=(0, 10))
        
        self.status_label = ctk.CTkLabel(self, text="", text_color="red", font=ctk.CTkFont(size=12))
        self.status_label.pack(pady=10)
        
        self.login_btn = ctk.CTkButton(self, text="Bejelentkezés és mentés", width=320, height=40, fg_color="#005baa", hover_color="#00437d", font=ctk.CTkFont(weight="bold"), command=self.handle_login)
        self.login_btn.pack(pady=10)
        self.bind("<Return>", self.handle_login)

        copyright_text = "© 2026 Developed by Zoltan Biro | Tailored for Haier Promoting Team"
        ctk.CTkLabel(self, text=copyright_text, font=ctk.CTkFont(family="Arial", size=9), text_color="#444444").pack(side="bottom", pady=15)

    def handle_login(self, event=None):
        email = self.email_entry.get().strip()
        password = self.pass_entry.get().strip()
        
        if not email or not password:
            self.status_label.configure(text="Minden mezőt ki kell tölteni!", text_color="red")
            return
            
        self.login_btn.configure(state="disabled", text="Kapcsolódás...")
        self.status_label.configure(text="Adatok ellenőrzése a SalesPortal-on, kérlek várj...", text_color="orange")
        self.update_idletasks()
        self.unbind("<Return>")
        threading.Thread(target=self._login_worker, args=(email, password), daemon=True).start()

    def _login_worker(self, email, password):
        try:
            stores, weeks = fetch_stores_and_weeks(email, password)
            if stores:
                auth.save_credentials(email, password)
                self.credentials = {"email": email, "password": password}
                self.after(0, lambda: self.build_main_ui(stores, weeks))
            else:
                self.after(0, lambda: self._login_failed("Sikertelen belépés! Hibás email vagy jelszó."))
        except Exception:
            self.after(0, lambda: self._login_failed("Hálózati hiba! A SalesPortal nem érhető el."))

    def _login_failed(self, error_message):
        self.login_btn.configure(state="normal", text="Mentés és kapcsolódás")
        self.status_label.configure(text=error_message, text_color="red")
        self.bind("<Return>", self.handle_login)

    def preload_data(self):
        self.clear_ui()
        
        logo_path = get_asset_path(os.path.join("assets", "haier.png"))
        if os.path.exists(logo_path):
            self.original_image = Image.open(logo_path).convert("RGBA")
            self.pulse_label = ctk.CTkLabel(self, text="", fg_color="transparent")
            self.pulse_label.pack(pady=(230, 10))
            self.logo_opacity, self.pulse_direction = 1.0, -0.04
            self.animate_pulse()

        self.progress_bar = ctk.CTkProgressBar(self, width=300, height=4, fg_color="#1E1E1E", progress_color="#005baa")
        self.progress_bar.pack(pady=(20, 10))
        self.progress_bar.set(0.0)

        self.loading_label = ctk.CTkLabel(self, text="SZOFTVER INDÍTÁSA...", font=ctk.CTkFont(family="Arial", size=10, weight="bold"), text_color="#FFFFFF")
        self.loading_label.pack(pady=5)
        
        copyright_text = "© 2026 Developed by Zoltan Biro | Tailored for Haier Promoting Team"
        ctk.CTkLabel(self, text=copyright_text, font=ctk.CTkFont(family="Arial", size=11), text_color="#555555").pack(side="bottom", pady=15)
        
        self.update()
        threading.Thread(target=self._preload_worker, daemon=True).start()

    def _preload_update_ui(self, text, value):
        self.after(0, lambda: self.loading_label.configure(text=text.upper()))
        self.after(0, lambda: self.progress_bar.set(value))

    def _preload_worker(self):
        try:
            stores, weeks = fetch_stores_and_weeks(self.credentials["email"], self.credentials["password"], status_callback=self._preload_update_ui)
            if hasattr(self, '_pulse_job'): self.after_cancel(self._pulse_job)
            if stores: self.after(0, lambda: self.build_main_ui(stores, weeks))
            else: self.after(0, self.build_login_ui)
        except Exception:
            if hasattr(self, '_pulse_job'): self.after_cancel(self._pulse_job)
            self.after(0, self.build_login_ui)

    def animate_pulse(self):
        if not hasattr(self, 'original_image') or not hasattr(self, 'pulse_label'): return
        self.logo_opacity += self.pulse_direction
        if self.logo_opacity >= 1.0 or self.logo_opacity <= 0.3: self.pulse_direction *= -1
        r, g, b, a = self.original_image.split()
        a = a.point(lambda p: int(p * self.logo_opacity))
        ctk_img = ctk.CTkImage(light_image=Image.merge("RGBA", (r, g, b, a)), dark_image=Image.merge("RGBA", (r, g, b, a)), size=(300, 93))
        self.pulse_label.configure(image=ctk_img)
        self.pulse_label._image = ctk_img
        self._pulse_job = self.after(40, self.animate_pulse)

    def build_main_ui(self, stores, weeks):
        self.clear_ui()
        logo_path = get_asset_path(os.path.join("assets", "haier.png"))
        if os.path.exists(logo_path):
            raw_img = Image.open(logo_path)
            logo_img = ctk.CTkImage(light_image=raw_img, dark_image=raw_img, size=(300, 93))
            ctk.CTkLabel(self, text="", image=logo_img).pack(pady=(40, 5))

        ctk.CTkLabel(self, text="SalesPortal Merchandising Riport", font=ctk.CTkFont(family="Arial", size=16, weight="bold")).pack(pady=(0, 15))

        # Áruház és Hét választó
        ctk.CTkLabel(self, text="Áruház kiválasztása:", font=ctk.CTkFont(size=12)).pack(pady=2)
        self.store_combo = ctk.CTkComboBox(self, values=stores, width=400, state="readonly", command=self.on_store_selected)
        self.store_combo.pack(pady=5)
        if os.getenv("STORE_NAME") in stores: self.store_combo.set(os.getenv("STORE_NAME"))

        ctk.CTkLabel(self, text="Riport hete:", font=ctk.CTkFont(size=12)).pack(pady=2)
        self.week_combo = ctk.CTkComboBox(self, values=weeks, width=400, state="readonly")
        self.week_combo.pack(pady=5)
        current_iso_week = str(datetime.now().isocalendar()[1])
        if current_iso_week in weeks: self.week_combo.set(current_iso_week)

        # Tallózás és Státusz
        self.btn_browse = ctk.CTkButton(self, text="WAWI-s Excel fájlok kiválasztása", width=250, height=35, fg_color="#005baa", hover_color="#00437d", font=ctk.CTkFont(weight="bold"), command=self.browse_files)
        self.btn_browse.pack(pady=15)
        self.file_status_label = ctk.CTkLabel(self, text="Nincs fájl kiválasztva.", text_color="#005baa", font=ctk.CTkFont(weight="bold"))
        self.file_status_label.pack(pady=(0, 10))

        # Táblázat Előnézet
        self.preview_label = ctk.CTkLabel(self, text="Fájl(ok) előnézete (első 5 sor):", font=ctk.CTkFont(family="Arial", size=13, weight="bold"), text_color="gray", anchor="w")
        self.preview_label.pack(pady=(15, 0), padx=75, fill="x")

        # STÍLUS ÉS TÁBLÁZAT MEGHÍVÁSA A STYLES MODULBÓL
        apply_treeview_style(self)
        self.tree = ttk.Treeview(self, columns=("Modell", "Raktárhely", "Mennyiség"), show="headings", height=5, style="Treeview")
        self.tree.heading("Modell", text="Modell név", anchor="w")
        self.tree.heading("Raktárhely", text="Kiállított?", anchor="center")
        self.tree.heading("Mennyiség", text="Készlet (db)", anchor="center")
        self.tree.column("Modell", width=350, anchor="w")
        self.tree.column("Raktárhely", width=180, anchor="center")
        self.tree.column("Mennyiség", width=120, anchor="center")
        self.tree.pack(pady=(5, 15), padx=50)

        # INDÍTÁS GOMB
        self.btn_run = ctk.CTkButton(self, text="ROBOT INDÍTÁSA", width=250, height=40, font=ctk.CTkFont(size=14, weight="bold"), fg_color="green", hover_color="darkgreen", command=self.run_bot_logic)
        self.btn_run.pack(pady=15)
        
        # COPYRIGHT LÁBLÉC
        copyright_text = "© 2026 Developed by Zoltan Biro | Tailored for Haier Promoting Team"
        copyright_label = ctk.CTkLabel(self, text=copyright_text, font=ctk.CTkFont(family="Arial", size=9), text_color="#444444")
        copyright_label.pack(side="bottom", pady=(10, 15)) # 15 pixel az ablak aljától

        # KIJELENTKEZÉS GOMB
        btn_logout = ctk.CTkButton(self, text="Kijelentkezés", width=180, height=25, fg_color="maroon", hover_color="red", command=self.logout)
        btn_logout.pack(side="bottom", pady=10)

    def on_store_selected(self, choice):
        self.week_combo.configure(state="normal", values=["Frissítés..."])
        self.week_combo.set("Frissítés...")
        self.week_combo.configure(state="disabled")
        self.update_idletasks()
        threading.Thread(target=self._update_weeks_worker, args=(choice,), daemon=True).start()

    def _update_weeks_worker(self, store_name):
        def combo_callback(text, value): self.after(0, lambda: self.week_combo.set(text))
        _, active_weeks = fetch_stores_and_weeks(self.credentials["email"], self.credentials["password"], selected_store=store_name, status_callback=combo_callback)
        self.after(0, lambda: self._apply_new_weeks(active_weeks))

    def _apply_new_weeks(self, active_weeks):
        if active_weeks:
            current_iso_week = str(datetime.now().isocalendar()[1])
            self.week_combo.configure(state="readonly", values=active_weeks)
            self.week_combo.set(current_iso_week if current_iso_week in active_weeks else active_weeks[0])
        else:
            self.week_combo.configure(state="readonly", values=["Nincs elérhető hét"])
            self.week_combo.set("Nincs elérhető hét")

    def browse_files(self):
        home_path = os.path.expanduser("~")
        default_path = os.path.join(home_path, "Downloads")
        if not os.path.exists(default_path):
            default_path = os.path.join(home_path, "Letöltések") if os.path.exists(os.path.join(home_path, "Letöltések")) else home_path

        files = filedialog.askopenfilenames(title="Válaszd ki a WAWI fájlokat", initialdir=default_path, filetypes=[("Excel fájlok", "*.xls *.xlsx")])
        if files:
            self.selected_files = list(files)
            all_data_list = [get_excel_data(f) for f in self.selected_files if get_excel_data(f) is not None]
            if all_data_list:
                self.final_dataframe = pd.concat(all_data_list, ignore_index=True).sort_values(by=['modellnev', 'raktar_hely'], ascending=[True, True]).drop_duplicates(subset=['modellnev'], keep='first')
                self.file_status_label.configure(text=f"{len(self.selected_files)} db fájl betöltve ({len(self.final_dataframe)} db egyedi modell).", text_color="green")
                self.update_table_preview()
            else:
                CTkMessagebox(title="Hiba", message="A kijelölt fájlokból nem lehetett adatot kiolvasni!", icon="cancel")

    def update_table_preview(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for _, row in self.final_dataframe.head(5).iterrows():
            loc_str = str(row.get('raktar_hely', '-')).strip()
            loc = "Igen" if loc_str == "5" else ("Nem" if loc_str == "6" else (f"Egyéb ({loc_str})" if loc_str and loc_str != "-" else "-"))
            self.tree.insert("", "end", values=(row.get('modellnev', 'Ismeretlen'), loc, row.get('db', row.get('keszlet', 1))))
        self.tree.selection_remove(self.tree.selection())

    def run_bot_logic(self):
        if not self.store_combo.get():
            CTkMessagebox(title="Hiányzó áruház", message="Kérlek, válassz ki egy áruházat!", icon="warning")
            return
        if self.final_dataframe is None or self.final_dataframe.empty:
            CTkMessagebox(title="Hiányzó fájl(ok)", message="Kérlek, válassz ki fájlokat!", icon="warning")
            return
        self.btn_run.configure(state="disabled", text="ROBOT FUT...")
        threading.Thread(target=self.execute_playwright, args=(self.store_combo.get(), self.week_combo.get(), self.final_dataframe), daemon=True).start()

    def execute_playwright(self, store, week, final_data):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, args=["--start-maximized"])
            page = browser.new_context(no_viewport=True).new_page()
            try:
                page.goto("https://salesportal.salesninja.hu/login")
                page.fill("input[name='email']", self.credentials["email"])
                page.fill("input[name='password']", self.credentials["password"])
                page.click("button[type='submit']")
                page.wait_for_load_state("domcontentloaded")
                merch_report(page, store, week, final_data)
                page.wait_for_event("close", timeout=0)
            except Exception as e: print(f"Hiba: {e}")
            finally: browser.close()
        self.after(0, lambda: self.btn_run.configure(state="normal", text="ROBOT INDÍTÁSA"))

    def logout(self):
        if os.path.exists(auth.CONFIG_FILE): os.remove(auth.CONFIG_FILE)
        if os.path.exists(auth.KEY_FILE): os.remove(auth.KEY_FILE)
        self.credentials = None
        self.build_login_ui()

    def clear_ui(self):
        for widget in self.winfo_children(): widget.pack_forget()

if __name__ == "__main__":
    SalesBotGUI().mainloop()