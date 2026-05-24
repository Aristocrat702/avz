import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
from recon.scanner import ReconScanner
from gui.widgets import RightClickMenu

class ReconTab:
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="🔎 Разведка")
        self.scanner = ReconScanner(log_callback=self._log, progress_callback=self._update_progress)
        self.current_report = None
        self._stop_requested = False
        self._build_ui()
        self.app.logger.info("Вкладка Разведки инициализирована")

    def _build_ui(self):
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(2, weight=1)

        top = ttk.Frame(self.frame)
        top.grid(row=0, column=0, sticky='ew', padx=10, pady=5)
        ttk.Label(top, text="Цель:").pack(side=tk.LEFT)
        self.target_entry = ttk.Entry(top, width=50)
        self.target_entry.pack(side=tk.LEFT, padx=5)
        RightClickMenu(self.target_entry)
        ttk.Button(top, text="📋", width=3, command=lambda: self.target_entry.insert(0, self.app.root.clipboard_get())).pack(side=tk.LEFT)
        self.scan_all_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="Все порты", variable=self.scan_all_var).pack(side=tk.LEFT, padx=5)
        self.nuclei_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="Nuclei", variable=self.nuclei_var).pack(side=tk.LEFT, padx=5)
        self.amass_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="Amass", variable=self.amass_var).pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="🔍 Сканировать", command=self._start_recon).pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(top, text="⏹ Стоп", command=self._stop_recon, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="💾 PDF", command=self._export_pdf).pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="⚡ Атаковать уязвимости", command=self._attack_vulnerabilities).pack(side=tk.RIGHT, padx=10)
        self.recon_progress = ttk.Progressbar(top, length=150, mode='determinate')
        self.recon_progress.pack(side=tk.RIGHT, padx=10)

        self.output = scrolledtext.ScrolledText(self.frame, bg='#1e1e1e' if self.app.theme=='dark' else 'white',
                                                fg=self.app.fg, wrap=tk.WORD)
        self.output.grid(row=2, column=0, sticky='nsew', padx=10, pady=5)
        RightClickMenu(self.output, get_text_func=lambda: self.output.get("1.0", tk.END).strip())
        self.output.tag_configure("heading", font=("Arial",12,"bold"), foreground="cyan")
        self.output.tag_configure("ok", foreground="green")
        self.output.tag_configure("warn", foreground="orange")

    def _start_recon(self):
        target = self.target_entry.get().strip()
        if not target:
            messagebox.showerror("Ошибка", "Введите цель")
            return
        self.output.delete(1.0, tk.END)
        self.recon_progress['value'] = 0
        self.stop_btn.config(state=tk.NORMAL)
        self._stop_requested = False
        self.output.insert(tk.END, "🔍 Разведка начата...\n")
        self.app.logger.info(f"Разведка: {target}")
        threading.Thread(target=self._run_recon, args=(target,), daemon=True).start()

    def _run_recon(self, target):
        try:
            scan_all = self.scan_all_var.get()
            use_nuclei = self.nuclei_var.get()
            use_amass = self.amass_var.get()
            self.current_report = self.scanner.full_report(target, scan_all, use_nuclei, use_amass)
            self.frame.after(0, lambda: self._display_report(self.current_report))
            self.app.logger.info(f"Разведка завершена: {target}")
        except Exception as e:
            self.app.logger.error(f"Ошибка разведки: {e}")
            self.frame.after(0, lambda: self.output.insert(tk.END, f"❌ Критическая ошибка: {e}\n"))
        finally:
            self.frame.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
            self.frame.after(0, lambda: self.recon_progress.config(value=100))

    def _stop_recon(self):
        self._stop_requested = True
        self.scanner.stop()
        self.stop_btn.config(state=tk.DISABLED)
        self.output.insert(tk.END, "[!] Разведка остановлена.\n")

    def _display_report(self, report):
        out = self.output
        out.insert(tk.END, f"\n=== Разведка: {report.get('target')} ===\n\n", "heading")
        out.insert(tk.END, f"🌐 IP: {', '.join(report.get('ips', []))}\n")
        out.insert(tk.END, f"📍 Geo: {report.get('geo')}\n")
        out.insert(tk.END, f"⏱ Пинг: {report.get('ping')}\n")
        out.insert(tk.END, f"🏢 Whois: {report.get('whois')}\n\n")
        http = report.get('http', {})
        out.insert(tk.END, f"🌍 Сервер: {http.get('server')}\n")
        cf = http.get('cloudflare')
        out.insert(tk.END, f"Cloudflare: {'Да ⚠️' if cf else 'Нет ✅'}\n", "warn" if cf else "ok")
        out.insert(tk.END, f"robots.txt: {http.get('robots.txt')}\n")
        out.insert(tk.END, f"sitemap.xml: {http.get('sitemap.xml')}\n\n")
        subs = report.get('subdomains', [])
        if subs:
            out.insert(tk.END, f"🔗 Поддомены ({len(subs)}): {', '.join(subs)}\n\n")
        techs = report.get('technologies', [])
        out.insert(tk.END, f"📊 Технологии: {', '.join(techs) if techs else 'не определены'}\n\n")
        cve_list = report.get('cve', [])
        if cve_list:
            out.insert(tk.END, "🛡 Найденные CVE:\n", "heading")
            for cve in cve_list:
                out.insert(tk.END, f"{cve['id']}: {cve['title']} (CVSS: {cve['cvss']})\n")
        nuclei = report.get('nuclei', [])
        if nuclei:
            out.insert(tk.END, "\n🧪 Nuclei результаты:\n", "heading")
            for n in nuclei:
                out.insert(tk.END, f"{n['template']}: {n['name']} ({n['severity']}) -> {n['matched']}\n")
        vuln = report.get('vuln', {})
        out.insert(tk.END, f"\nSQLi: {'Обнаружена ⚠️' if vuln.get('sqli') else 'Не обнаружена'}\n", "warn" if vuln.get('sqli') else "ok")
        out.insert(tk.END, f"XSS: {'Обнаружена ⚠️' if vuln.get('xss') else 'Не обнаружена'}\n\n", "warn" if vuln.get('xss') else "ok")
        ports = report.get('ports', [])
        if ports:
            out.insert(tk.END, f"🔓 Открытые порты: {', '.join(map(str, ports))}\n")
        else:
            out.insert(tk.END, "🔓 Открытых портов не найдено\n")
        # Рекомендация
        out.insert(tk.END, "\n💡 Рекомендация по атаке:\n", "heading")
        http = report.get('http', {})
        if http.get('cloudflare'):
            out.insert(tk.END, "Обнаружен Cloudflare → используйте CFBUAM с FlareSolverr или JA3 chrome120\n")
        elif 'WordPress' in str(report.get('technologies', [])):
            out.insert(tk.END, "WordPress → попробуйте POST на /xmlrpc.php (пресет WordPress Breaker)\n")
        else:
            out.insert(tk.END, "Рекомендуется начать с CFBUAM или GET с включённым браузерным штормом\n")

    def _export_pdf(self):
        if not self.current_report:
            messagebox.showwarning("Нет данных", "Сначала выполните разведку")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files","*.pdf")])
        if filename:
            self.scanner.export_pdf(self.current_report, filename)
            self.app.logger.info(f"PDF-отчёт сохранён: {filename}")
            messagebox.showinfo("Готово", f"PDF-отчёт сохранён в {filename}")

    def _attack_vulnerabilities(self):
        if not self.current_report:
            messagebox.showwarning("Нет данных", "Сначала выполните разведку")
            return
        report = self.current_report
        target = report.get('target', '')
        techs = report.get('technologies', [])
        http = report.get('http', {})
        if 'WordPress' in techs:
            endpoints = [("/xmlrpc.php", "POST")]
        elif http.get('cloudflare'):
            endpoints = [("/", "CFBUAM")]
        else:
            endpoints = [("/", "GET")]
        path, method = endpoints[0]
        full_url = target.rstrip('/') + path
        attack_tab = self.app.attack_tab
        attack_tab.target_entry.delete(0, tk.END)
        attack_tab.target_entry.insert(0, full_url)
        attack_tab.method_var.set(method)
        if http.get('cloudflare'):
            attack_tab.flare_url_var.set("http://localhost:8191/v1")
            attack_tab.ja3_var.set("chrome120")
        attack_tab.threads_var.set(200)
        self.app.notebook.select(0)
        messagebox.showinfo("Готово", f"Цель и метод ({method}) перенесены в Атаку. Нажмите 'Запустить'")

    def _log(self, msg):
        self.output.insert(tk.END, msg)
        self.output.see(tk.END)
        self.frame.update_idletasks()

    def _update_progress(self, val):
        self.recon_progress['value'] = val
        self.frame.update_idletasks()