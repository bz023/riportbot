import os
import sys
from tkinter import ttk
import customtkinter as ctk

def get_asset_path(relative_path):
    """Visszaadja a fájl pontos elérését, függetlenül attól, hogy kódból vagy .exe-ből fut"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def apply_treeview_style(root):
    """Beállítja a gyönyörű, sötét tónusú modern táblázatstílust"""
    custom_bg_pair = ["#EAEAEA", "#1A1A1A"]
    bg_color = root._apply_appearance_mode(custom_bg_pair)
    text_color = root._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
    accent_color = root._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
    selected_text = root._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["text_color"])
    header_bg = root._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])

    style = ttk.Style()
    style.theme_use("clam")
    style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
    
    style.configure(
        "Treeview", 
        background=bg_color, foreground=text_color, fieldbackground=bg_color, 
        rowheight=25, borderwidth=0, highlightthickness=0, relief="flat"
    )
    style.configure(
        "Treeview.Heading", 
        background=header_bg, foreground=text_color, 
        font=("Arial", 11, "bold"), borderwidth=1, relief="flat"
    )
    style.map("Treeview", background=[('selected', accent_color)], foreground=[('selected', selected_text)])