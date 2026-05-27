import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json, os, threading, asyncio
from utils.widgets import ToolTip

class ConstructorTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.sequence = []
        self.build_ui()

    def build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(top, text="Последовательность атак").pack(side=tk.LEFT)
        add_btn = ttk.Button(top, text="+ Добавить шаг", command=self.add_step)
        add_btn.pack(side=tk.RIGHT, padx=5)
        ToolTip(add_btn, "Добавить вектор в очередь")

        self.listbox = tk.Listbox(self, height=10)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        mode_frame = ttk.Frame(self)
        mode_frame.pack()
        self.parallel_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(mode_frame, text="Параллельное выполнение", variable=self.parallel_var).pack(side=tk.LEFT)

        btn_frame = ttk.Frame(self)
        btn_frame.pack()
        run_btn = ttk.Button(btn_frame, text="Запустить цепочку", command=self.run_sequence)
        run_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(run_btn, "Выполнить все шаги по порядку или параллельно")
        save_btn = ttk.Button(btn_frame, text="Сохранить", command=self.save)
        save_btn.pack(side=tk.LEFT, padx=5)
        load_btn = ttk.Button(btn_frame, text="Загрузить", command=self.load)
        load_btn.pack(side=tk.LEFT, padx=5)
        clear_btn = ttk.Button(btn_frame, text="Очистить", command=self.clear)
        clear_btn.pack(side=tk.LEFT, padx=5)
        self.status = ttk.Label(self, text="")
        self.status.pack()

    def add_step(self):
        dialog = tk.Toplevel(self)
        dialog.title("Новый шаг")
        ttk.Label(dialog, text="Метод:").grid(row=0, column=0)
        method_var = tk.StringVar(value="syn")
        methods = ["udp","tcp","syn","icmp","http","dns_amp","multivector"]
        ttk.Combobox(dialog, textvariable=method_var, values=methods).grid(row=0, column=1)
        ttk.Label(dialog, text="Цель:").grid(row=1, column=0)
        target_entry = ttk.Entry(dialog, width=25)
        target_entry.grid(row=1, column=1)
        ttk.Label(dialog, text="Порт:").grid(row=2, column=0)
        port_entry = ttk.Entry(dialog, width=6)
        port_entry.insert(0, "80")
        port_entry.grid(row=2, column=1, sticky=tk.W)
        ttk.Label(dialog, text="Длительность (с):").grid(row=3, column=0)
        dur_entry = ttk.Entry(dialog, width=6)
        dur_entry.insert(0, "30")
        dur_entry.grid(row=3, column=1, sticky=tk.W)
        def confirm():
            self.sequence.append({
                'method': method_var.get(),
                'target': target_entry.get(),
                'port': int(port_entry.get()),
                'duration': int(dur_entry.get())
            })
            self.listbox.insert(tk.END, f"{method_var.get()} -> {target_entry.get()}:{port_entry.get()} [{dur_entry.get()}c]")
            dialog.destroy()
        ttk.Button(dialog, text="OK", command=confirm).grid(row=4, columnspan=2, pady=10)

    def run_sequence(self):
        if not self.sequence:
            messagebox.showwarning("Пусто", "Добавьте хотя бы один шаг")
            return
        self.status.config(text="Выполнение цепочки...")
        threading.Thread(target=self._run_seq).start()

    def _run_seq(self):
        from engine.attack import AsyncAttackEngine
        engine = AsyncAttackEngine()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        if self.parallel_var.get():
            tasks = [engine.run_attack(s['method'], s['target'], s['port'], s['duration']) for s in self.sequence]
            loop.run_until_complete(asyncio.gather(*tasks))
        else:
            for step in self.sequence:
                loop.run_until_complete(engine.run_attack(step['method'], step['target'], step['port'], step['duration']))
        self.status.config(text="Цепочка завершена")

    def save(self):
        filename = simpledialog.askstring("Сохранить", "Имя файла:")
        if filename:
            os.makedirs("chains", exist_ok=True)
            with open(f"chains/{filename}.json", "w") as f:
                json.dump(self.sequence, f)
            messagebox.showinfo("Сохранено", f"Цепочка сохранена как chains/{filename}.json")

    def load(self):
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(initialdir="chains", filetypes=[("JSON", "*.json")])
        if filepath:
            with open(filepath, "r") as f:
                self.sequence = json.load(f)
            self.listbox.delete(0, tk.END)
            for s in self.sequence:
                self.listbox.insert(tk.END, f"{s['method']} -> {s['target']}:{s['port']} [{s['duration']}c]")
            messagebox.showinfo("Загружено", f"Загружено {len(self.sequence)} шагов")

    def clear(self):
        self.sequence.clear()
        self.listbox.delete(0, tk.END)
