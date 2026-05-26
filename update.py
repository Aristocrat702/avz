#!/usr/bin/env python3
import json, os, sys

def check_syntax(content, filename):
    """Проверяет, является ли content корректным Python-кодом."""
    if not filename.endswith('.py'):
        return True
    try:
        compile(content, filename, 'exec')
        return True
    except SyntaxError as e:
        print(f"[!] Синтаксическая ошибка в {filename}:\n{e}")
        return False

def apply_manifest(manifest_path):
    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    files = data.get('files', {})
    if not files:
        print("Нет файлов для обновления.")
        return

    # Проверяем синтаксис всех Python-файлов
    syntax_ok = True
    for path, content in files.items():
        if not check_syntax(content, path):
            syntax_ok = False
    if not syntax_ok:
        print("\n[!] Обновление отменено из-за синтаксических ошибок.")
        sys.exit(1)

    # Записываем файлы
    for path, content in files.items():
        full_path = os.path.join(os.getcwd(), path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] {path}")
    print("\n✅ Готово. Запустите main.py")

if __name__ == "__main__":
    apply_manifest("manifest.json")
