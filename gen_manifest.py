import os, json

manifest = {"files": {}}
for root, dirs, files in os.walk('.'):
    if '__pycache__' in root or '.git' in root:
        continue
    for file in files:
        if file.endswith('.py') or file.endswith('.json'):
            path = os.path.join(root, file).replace('\\', '/')
            if path.startswith('./'):
                path = path[2:]
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            manifest['files'][path] = content
with open('manifest.json', 'w', encoding='utf-8') as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
print('manifest.json создан')