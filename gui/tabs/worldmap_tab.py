import tkinter as tk
from tkinter import ttk
import folium
import webbrowser
import json
import os

class WorldMapTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        ttk.Button(self, text="Показать карту мира", command=self.show_map).pack(pady=20)

    def show_map(self):
        # Читаем bots.json
        bots = []
        if os.path.exists('bots.json'):
            with open('bots.json') as f:
                data = json.load(f)
                for b in data:
                    if isinstance(b, dict) and 'lat' in b and 'lon' in b:
                        bots.append((b['lat'], b['lon'], b.get('id','?')))
        m = folium.Map(location=[0, 0], zoom_start=2)
        for lat, lon, bid in bots:
            folium.Marker([lat, lon], popup=bid).add_to(m)
        m.save('worldmap.html')
        webbrowser.open('worldmap.html')
