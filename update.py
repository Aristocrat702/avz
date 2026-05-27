import json
import os
import shutil
import sys
import subprocess

MANIFEST_FILE = "manifest.json"
# Файлы, которые нельзя перезаписывать при обновлении
PROTECTED_FILES = {
    "bots.json",
    "attack_history.db",
    "secrets.json",
    "avz_state.json",
    "attack_profiles.json",
    "ssh_nodes.json",
    "avz.log",
    "loot/"
}

def apply_manifest():
    if not os.path.exists(MANIFEST_FILE):
        print("[!] manifest.json не найден")
        return

    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    files = data.get("files", [])
    for entry in files:
        path = entry["path"]
        content = entry["content"]

        # Пропускаем защищённые файлы
        if path in PROTECTED_FILES:
            print(f"[✓] Пропущен защищённый файл: {path}")
            continue

        dir_path = os.path.dirname(path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[+] Обновлён: {path}")

    # Установка зависимостей
    if os.path.exists("requirements.txt"):
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("[+] Зависимости установлены")

    # Удаляем манифест после применения
    os.remove(MANIFEST_FILE)
    print("[✓] Обновление завершено. Удали манифест и перезапусти программу.")

if __name__ == "__main__":
    apply_manifest()