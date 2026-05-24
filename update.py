import json, os

MANIFEST = "manifest.json"
with open(MANIFEST, "r", encoding="utf-8") as f:
    data = json.load(f)

for path, content in data["files"].items():
    full_path = os.path.join(os.getcwd(), path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] {path}")

print("\n✅ Все файлы из манифеста успешно записаны. Запустите main.py.")