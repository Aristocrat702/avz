import requests
import json
import os
import subprocess
import sys

GITHUB_REPO = "Aristocrat702/avz"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

def get_latest_version():
    try:
        resp = requests.get(GITHUB_API)
        resp.raise_for_status()
        release = resp.json()
        return release['tag_name'], release['assets']
    except Exception as e:
        print(f"Не удалось проверить обновления: {e}")
        return None, []

def download_asset(url, filename):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def apply_update():
    latest, assets = get_latest_version()
    if not latest:
        return False
    # Проверяем, не установлена ли уже эта версия
    current_version = None
    if os.path.exists('version.json'):
        with open('version.json') as f:
            data = json.load(f)
            current_version = data.get('version')
    if current_version == latest:
        print("Уже установлена последняя версия")
        return False
    # Ищем манифест среди ассетов
    manifest_url = None
    for asset in assets:
        if asset['name'] == 'manifest.json':
            manifest_url = asset['browser_download_url']
            break
    if not manifest_url:
        print("Манифест не найден в релизе")
        return False
    download_asset(manifest_url, 'manifest.json')
    # Применяем манифест
    subprocess.run([sys.executable, 'update.py'])
    return True

if __name__ == '__main__':
    apply_update()
