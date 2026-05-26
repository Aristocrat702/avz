import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import threading, paramiko, socket, json, time, os, sys, io, ast, importlib, inspect

class DiagnosticTab(ttk.Frame):
    def __init__(self, parent, app=None):
        super().__init__(parent)
        self.app = app
        self.vps_host = "80.249.146.202"
        self.vps_user = "root"
        self.vps_pass = None
        self.create_widgets()

    def create_widgets(self):
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="Диагностика VPS", command=self.run_diag).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Автоисправление VPS", command=self.run_repair).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Проверить порт 80", command=self.check_port).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Анализ кода", command=self.run_code_analysis).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Создать вкладку", command=self.create_tab_wizard).pack(side=tk.LEFT, padx=2)

        self.log = scrolledtext.ScrolledText(self, height=10, bg='white', font=('Consolas', 9))
        self.log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        console_frame = ttk.LabelFrame(self, text="Python-консоль (быстрые проверки)")
        console_frame.pack(fill=tk.X, padx=5, pady=5)
        self.code_entry = tk.Text(console_frame, height=4, bg='#ffffcc', font=('Consolas', 10))
        self.code_entry.pack(fill=tk.X, padx=5, pady=2)
        self.code_entry.insert(tk.END, "s = socket.socket(); s.settimeout(3); s.connect(('80.249.146.202',80)); s.sendall(b'list'); print(s.recv(4096).decode())")
        ttk.Button(console_frame, text="Выполнить код", command=self.exec_python).pack(pady=2)

    # ------------------- Генератор вкладок -------------------
    def create_tab_wizard(self):
        class_name = simpledialog.askstring("Новая вкладка", "Имя класса (например, TestTab):")
        if not class_name:
            return
        tab_title = simpledialog.askstring("Заголовок вкладки", "Заголовок для интерфейса (например, Тест):")
        if not tab_title:
            return

        # Формируем код нового файла
        file_name = class_name.lower().rstrip('tab') + '_tab.py'
        content = f'''import tkinter as tk
from tkinter import ttk

class {class_name}(ttk.Frame):
    def __init__(self, parent, app=None):
        super().__init__(parent)
        self.app = app
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="{tab_title}", font=("Arial", 12)).pack(pady=20)
        # Добавьте элементы интерфейса здесь
'''
        # Записываем файл
        tabs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '')
        file_path = os.path.join(tabs_dir, file_name)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать файл: {e}")
            return

        # Добавляем импорт и вкладку в app.py
        app_path = os.path.join(os.path.dirname(tabs_dir), 'app.py')
        try:
            with open(app_path, 'r', encoding='utf-8') as f:
                app_code = f.read()
        except:
            messagebox.showerror("Ошибка", "Не удалось прочитать app.py")
            return

        # Добавляем импорт (после последнего импорта из gui.tabs)
        import_line = f"from gui.tabs.{file_name[:-3]} import {class_name}\n"
        if import_line not in app_code:
            # Ищем место для вставки: после последнего импорта из gui.tabs
            last_import = None
            lines = app_code.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('from gui.tabs.'):
                    last_import = i
            if last_import is not None:
                lines.insert(last_import + 1, import_line.rstrip('\n'))
                app_code = '\n'.join(lines)

        # Добавляем вкладку в tabs
        tabs_dict_pattern = '"Диагностика": DiagnosticTab,'
        if tabs_dict_pattern in app_code:
            new_tab_entry = f'            "{tab_title}": {class_name},\n'
            app_code = app_code.replace(tabs_dict_pattern, f'{new_tab_entry}            {tabs_dict_pattern}')

        # Сохраняем обновлённый app.py
        with open(app_path, 'w', encoding='utf-8') as f:
            f.write(app_code)

        messagebox.showinfo("Готово", f"Вкладка {class_name} создана в {file_name} и добавлена в app.py.\nПерезапустите программу.")
        self.log.insert(tk.END, f"[+] Создана вкладка {class_name} в {file_name}\n")

    # ------------------- Остальные методы (диагностика, автоисправление, консоль, анализ кода) уже были и остаются без изменений -------------------
    # ... (копируются из предыдущей версии diagnostic_tab.py)
