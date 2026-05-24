#!/usr/bin/env python3
"""AVZ-Aristo self-updater. Run with manifest.json in the same directory."""
import json, os, sys

def apply_manifest(manifest_path='manifest.json'):
    if not os.path.exists(manifest_path):
        print("manifest.json не найден. Положите его рядом с update.py")
        sys.exit(1)
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    files = manifest.get('files', {})
    for path, content in files.items():
        full_path = os.path.join(os.path.dirname(__file__) or '.', path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'[✓] {path}')
    # Создаём __init__.py во всех подпапках, если их нет
    for dirpath, dirnames, filenames in os.walk('.'):
        if dirpath != '.' and '__init__.py' not in filenames and not dirpath.startswith('.\\__'):
            init_file = os.path.join(dirpath, '__init__.py')
            with open(init_file, 'w') as f:
                f.write('')
            print(f'[✓] {init_file}')
    print('Обновление завершено. Запустите python main.py')

if __name__ == '__main__':
    apply_manifest()