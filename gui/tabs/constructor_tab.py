import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json, os, threading, asyncio
from utils.widgets import ToolTip
from tkinterdnd2 import DND_FILES, TkinterDnD

class DraggableBlock(tk.Frame):
    def __init__(self, parent, text, data, on_drag_end=None):
        super().__init__(parent, relief=tk.RAISED, bd=2)
        self.data = data
        self.label = ttk.Label(self, text=text)
        self.label.pack()
        self.bind("<ButtonPress-1>", self.start_drag)
        self.bind("<B1-Motion>", self.drag)
        self.bind("<ButtonRelease-1>", self.stop_drag)
        self.on_drag_end = on_drag_end
    def start_drag(self, event):
        self._start_x = event.x
        self._start_y = event.y
    def drag(self, event):
        x = self.winfo_x() + event.x - self._start_x
        y = self.winfo_y() + event.y - self._start_y
        self.place(x=x, y=y)
    def stop_drag(self, event):
        if self.on_drag_end:
            self.on_drag_end(self)

class ConstructorTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.sequence = []
        self.canvas = tk.Canvas(self, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.add_block_btn = ttk.Button(self, text="+ Добавить шаг", command=self.add_block)
        self.add_block_btn.place(x=10, y=10)
        self.run_btn = ttk.Button(self, text="Запустить", command=self.run_sequence)
        self.run_btn.place(x=150, y=10)
        self.blocks = []
    def add_block(self):
        self._create_block("SYN -> target", {"method":"syn"})
    def _create_block(self, text, data):
        block = DraggableBlock(self.canvas, text, data, self.on_drop)
        block.place(x=50+len(self.blocks)*150, y=50)
        self.blocks.append(block)
    def on_drop(self, block):
        # Реализация перетаскивания и перестроения цепочки
        pass
    def run_sequence(self):
        if not self.blocks:
            messagebox.showwarning("Пусто", "Добавьте шаги")
            return
        sequence = [b.data for b in self.blocks]
        threading.Thread(target=self._run_seq, args=(sequence,)).start()
    def _run_seq(self, sequence):
        from engine.attack import AsyncAttackEngine
        engine = AsyncAttackEngine()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        for step in sequence:
            loop.run_until_complete(engine.run_attack(step.get('method','syn'), step.get('target',''), 80, 60))
        messagebox.showinfo("Готово", "Цепочка завершена")
