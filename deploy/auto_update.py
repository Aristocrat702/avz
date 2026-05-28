import requests
import json
import os
import subprocess
import sys

GITHUB_REPO = "Aristocrat702/avz"
VERSION_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/version.json"
MANIFEST_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/manifest.json"

def get_remote_version():
    try:
        resp = requests.get(VERSION_URL, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('version')
    except Exception as e:
        print(f"Не удалось проверить обновления: {e}")
    return None

def get_local_version():
    if os.path.exists('version.json'):
        with open('version.json') as f:
            data = json.load(f)
            return data.get('version')
    return None

def download_manifest():
    resp = requests.get(MANIFEST_URL, timeout=30)
    if resp.status_code == 200:
        with open('manifest.json', 'w') as f:
            f.write(resp.text)
        return True
    return False

def apply_update():
    remote = get_remote_version()
    if not remote:
        print("Не удалось получить удалённую версию")
        return False
    local = get_local_version()
    if local and local >= remote:
        print(f"Версия {local} актуальна")
        return False
    print(f"Доступна новая версия: {remote}")
    if download_manifest():
        subprocess.run([sys.executable, 'update.py'])
        return True
    return False

if __name__ == '__main__':
    if apply_update():
        print("Обновление успешно применено!")
    else:
        print("Обновление не требуется")
