import tkinter as tk
from tkinter import ttk, messagebox
import os, datetime, zipfile

LOOT_DIR = "loot"

class LootTab:
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="🏆 Трофеи")
        # Создаём папку при необходимости
        os.makedirs(LOOT_DIR, exist_ok=True)
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=0)
        self.frame.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self.frame)
        toolbar.grid(row=0, column=0, sticky='ew', padx=10, pady=5)
        ttk.Button(toolbar, text="🔄 Обновить", command=self._refresh).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="📂 Открыть папку", command=self._open_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="📦 ZIP", command=self._export_zip).pack(side=tk.LEFT, padx=5)

        self.tree = ttk.Treeview(self.frame, columns=('size', 'date'), show='tree', selectmode='extended')
        self.tree.heading('#0', text='Имя')
        self.tree.heading('size', text='Размер')
        self.tree.heading('date', text='Дата')
        self.tree.column('#0', width=300)
        self.tree.column('size', width=100)
        self.tree.column('date', width=150)
        self.tree.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        scrollbar = ttk.Scrollbar(self.frame, orient='vertical', command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky='ns')
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.preview = tk.Text(self.frame, height=10, bg='#121212' if self.app.theme=='dark' else 'white',
                               fg=self.app.fg, state='disabled')
        self.preview.grid(row=2, column=0, sticky='nsew', padx=10, pady=5)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        if not os.path.isdir(LOOT_DIR):
            return
        for root, dirs, files in os.walk(LOOT_DIR):
            for file in files:
                fullpath = os.path.join(root, file)
                stat = os.stat(fullpath)
                size = f"{stat.st_size} B"
                date = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                relpath = os.path.relpath(fullpath, LOOT_DIR)
                iid = self.tree.insert('', 'end', text=relpath, values=(size, date), open=False)
                self.tree.item(iid, tags=(fullpath,))

    def _on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        tags = self.tree.item(iid, 'tags')
        if not tags:
            return
        fullpath = tags[0]
        try:
            with open(fullpath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(5000)
            self.preview.config(state='normal')
            self.preview.delete(1.0, tk.END)
            self.preview.insert(tk.END, content)
            self.preview.config(state='disabled')
        except:
            self.preview.config(state='normal')
            self.preview.delete(1.0, tk.END)
            self.preview.insert(tk.END, "(Невозможно прочитать файл)")
            self.preview.config(state='disabled')

    def _open_folder(self):
        os.startfile(LOOT_DIR)

    def _export_zip(self):
        if not os.path.isdir(LOOT_DIR):
            messagebox.showinfo("Пусто", "Нет файлов для экспорта")
            return
        zip_path = os.path.join(os.path.dirname(LOOT_DIR), f"loot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(LOOT_DIR):
                for file in files:
                    fullpath = os.path.join(root, file)
                    arcname = os.path.relpath(fullpath, LOOT_DIR)
                    zf.write(fullpath, arcname)
        messagebox.showinfo("Готово", f"Архив сохранён в {zip_path}")
