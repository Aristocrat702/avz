import tkinter as tk
from tkinter import ttk, scrolledtext
from web_hacking import SQLInjector, CMSScanner
import threading

class WebTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        # SQL Injection
        sql_frame = ttk.LabelFrame(self, text="SQL Инъектор")
        sql_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(sql_frame, text="URL:").grid(row=0, column=0)
        self.sql_url = ttk.Entry(sql_frame, width=40)
        self.sql_url.grid(row=0, column=1)
        ttk.Label(sql_frame, text="Cookie:").grid(row=1, column=0)
        self.sql_cookie = ttk.Entry(sql_frame, width=40)
        self.sql_cookie.grid(row=1, column=1)
        ttk.Label(sql_frame, text="POST Data:").grid(row=2, column=0)
        self.sql_data = ttk.Entry(sql_frame, width=40)
        self.sql_data.grid(row=2, column=1)
        btn_frame = ttk.Frame(sql_frame)
        btn_frame.grid(row=3, columnspan=2, pady=5)
        ttk.Button(btn_frame, text="Дамп БД", command=self.dump_db).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Список БД", command=self.list_dbs).pack(side=tk.LEFT, padx=2)

        # CMS Exploiter
        cms_frame = ttk.LabelFrame(self, text="CMS Эксплойтер")
        cms_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(cms_frame, text="URL сайта:").grid(row=0, column=0)
        self.cms_url = ttk.Entry(cms_frame, width=40)
        self.cms_url.grid(row=0, column=1)
        ttk.Button(cms_frame, text="Сканировать и взломать", command=self.exploit_cms).grid(row=1, columnspan=2, pady=5)

        # Output
        self.output = scrolledtext.ScrolledText(self, width=90, height=20)
        self.output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def dump_db(self):
        url = self.sql_url.get()
        if not url:
            return
        cookie = self.sql_cookie.get() or None
        data = self.sql_data.get() or None
        inj = SQLInjector(url, cookie, data)
        self.output.insert(tk.END, f"[SQLi] Запуск дампа...\n")
        threading.Thread(target=lambda: self._run_sql(inj, '--dump')).start()

    def list_dbs(self):
        url = self.sql_url.get()
        if not url:
            return
        cookie = self.sql_cookie.get() or None
        data = self.sql_data.get() or None
        inj = SQLInjector(url, cookie, data)
        self.output.insert(tk.END, f"[SQLi] Получение списка БД...\n")
        threading.Thread(target=lambda: self._run_sql(inj, '--dbs')).start()

    def _run_sql(self, inj, mode):
        result = inj.run(mode)
        self.output.insert(tk.END, result)

    def exploit_cms(self):
        url = self.cms_url.get()
        if not url:
            return
        scanner = CMSScanner(url)
        self.output.insert(tk.END, f"[CMS] Сканирование {url}...\n")
        threading.Thread(target=lambda: self._exploit_cms(scanner)).start()

    def _exploit_cms(self, scanner):
        cms = scanner.detect()
        if cms:
            self.output.insert(tk.END, f"[CMS] Найдена {cms}, запуск эксплойтов...\n")
            scanner.exploit()
        else:
            self.output.insert(tk.END, "[CMS] CMS не распознана.\n")
