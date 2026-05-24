import sys, argparse
import tkinter as tk

try:
    from tkinterdnd2 import TkinterDnD
    ROOT_CLASS = TkinterDnD.Tk
    DND_AVAILABLE = True
except ImportError:
    ROOT_CLASS = tk.Tk
    DND_AVAILABLE = False

from gui.app import App
from engine.attack import AsyncAttackEngine
from engine.proxy import ProxyManager
from recon.scanner import ReconScanner

def headless_attack(target, method, threads, proxy_file=None):
    proxies = []
    if proxy_file:
        with open(proxy_file) as f:
            proxies = [line.strip() for line in f if line.strip()]
    engine = AsyncAttackEngine(proxies)
    print(f"[*] Headless атака: {target} метод {method} потоков {threads}")
    engine.launch(target, method, threads)
    print(f"[✓] Атака завершена, запросов: {engine.stats['count']}")

def headless_recon(target, output_file=None):
    scanner = ReconScanner()
    report = scanner.full_report(target, scan_all_ports=False, use_nuclei=False, use_amass=False)
    if output_file:
        if output_file.endswith('.pdf'):
            scanner.export_pdf(report, output_file)
        else:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
        print(f"[✓] Отчёт сохранён в {output_file}")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AVZ-Aristo RAGE")
    parser.add_argument("--headless", action="store_true", help="Запуск без GUI")
    parser.add_argument("--target", help="Цель (URL/IP)")
    parser.add_argument("--method", default="CFBUAM", help="Метод атаки")
    parser.add_argument("--threads", type=int, default=100, help="Количество потоков")
    parser.add_argument("--proxy-file", help="Файл со списком прокси")
    parser.add_argument("--recon", action="store_true", help="Выполнить разведку")
    parser.add_argument("--output", help="Файл для сохранения отчёта (JSON или PDF)")
    args = parser.parse_args()

    if args.headless:
        if not args.target:
            print("Укажите --target для headless режима")
            sys.exit(1)
        if args.recon:
            headless_recon(args.target, args.output)
        else:
            headless_attack(args.target, args.method, args.threads, args.proxy_file)
    else:
        root = ROOT_CLASS()
        if DND_AVAILABLE:
            root.withdraw()
            root.update_idletasks()
            root.deiconify()
        app = App(root)
        root.mainloop()