import tkinter as tk
from tkinter import ttk
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import webbrowser, json, os

class StatsTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        ttk.Button(self, text="Generate Attack Report", command=self.report).pack(pady=10)
    def report(self):
        fig = make_subplots(rows=1, cols=2)
        fig.add_trace(go.Bar(x=['UDP','SYN','HTTP'], y=[120,200,90]), row=1, col=1)
        fig.write_html('report.html')
        webbrowser.open('report.html')
