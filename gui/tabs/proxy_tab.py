import tkinter as tk
from tkinter import ttk, messagebox
import json, os, threading, asyncio
from engine.proxy import ProxyManager

class ProxyTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pm = ProxyManager()
        self.build_ui()

    def build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True)

        list_frame = ttk.Frame(nb)
        nb.add(list_frame, text="Список")

        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        collect_btn = ttk.Button(btn_frame, text="Собрать прокси", command=self.collect_proxies)
        collect_btn.pack(side=tk.LEFT, padx=2)

        columns = ("Прокси", "Тип", "Статус")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.tree.heading("Прокси", text="Прокси")
        self.tree.heading("Тип", text="Тип")
        self.tree.heading("Статус", text="Статус")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.progress = ttk.Progressbar(list_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=5, pady=2)

        self.status_label = ttk.Label(list_frame, text="")
        self.status_label.pack()

        self.refresh_list()

        # Настройки
        settings_frame = ttk.Frame(nb)
        nb.add(settings_frame, text="Настройки")
        ttk.Label(settings_frame, text="Источники (один URL на строку):").pack(anchor=tk.W, padx=5, pady=5)
        self.sources_text = tk.Text(settings_frame, height=10)
        self.sources_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        try:
            with open("avz_settings.json", "r") as f:
                settings = json.load(f)
            for src in settings.get("proxy_sources", []):
                self.sources_text.insert(tk.END, src + "\n")
        except:
            pass
        ttk.Button(settings_frame, text="Сохранить источники", command=self.save_sources).pack(pady=5)

    def refresh_list(self):
        self.tree.delete(*self.tree.get_children())
        for p in self.pm.proxies:
            self.tree.insert("", tk.END, values=(p.get('url',''), p.get('type',''), "живой"))
        self.status_label.config(text=f"Всего: {len(self.pm.proxies)}")

    def collect_proxies(self):
        self.collect_btn.config(state=tk.DISABLED)
        self.progress.start()
        threading.Thread(target=self._collect).start()

    def _collect(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.pm.refresh_proxies())
        self.after(0, self._on_collect_done)

    def _on_collect_done(self):
        self.progress.stop()
        self.refresh_list()
        self.collect_btn.config(state=tk.NORMAL)
        messagebox.showinfo("Сбор прокси", f"Готово. Живых: {len(self.pm.proxies)}")

    def save_sources(self):
        sources = self.sources_text.get("1.0", tk.END).strip().split("\n")
        sources = [s.strip() for s in sources if s.strip()]
        try:
            with open("avz_settings.json", "r") as f:
                settings = json.load(f)
            settings["proxy_sources"] = sources
            with open("avz_settings.json", "w") as f:
                json.dump(settings, f, indent=2)
            messagebox.showinfo("Сохранено", "Источники обновлены")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
