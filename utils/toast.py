import tkinter as tk

def show_toast(parent, message, duration=3000):
    toast = tk.Toplevel(parent)
    toast.overrideredirect(True)
    toast.attributes('-topmost', True)
    label = tk.Label(toast, text=message, bg='black', fg='white', padx=20, pady=10)
    label.pack()
    toast.geometry('+{}+{}'.format(parent.winfo_rootx()+50, parent.winfo_rooty()+50))
    parent.after(duration, toast.destroy)
