from flask import Flask, request, jsonify
import subprocess, json, os, threading, time

app = Flask(__name__)

# Защищённый ключ для запросов от AVZ
API_SECRET = "pceeq1s8wv"  # совпадает с паролем VPS, можно сменить

MANIFEST_FILE = "manifest.json"

def apply_update():
    """Применяет полученный манифест"""
    if os.path.exists(MANIFEST_FILE):
        result = subprocess.run(["python3", "update.py"], capture_output=True, text=True)
        return result.stdout
    return "Нет манифеста"

@app.route('/improve', methods=['POST'])
def improve():
    data = request.json
    if data.get('secret') != API_SECRET:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    description = data.get('description', '')
    # Здесь должен быть вызов внешнего ИИ (например, DeepSeek API)
    # Пока возвращаем тестовый манифест для демонстрации
    response_manifest = {
        "files": [
            {
                "path": "test_improvement.txt",
                "content": f"Улучшение по запросу: {description}\nВремя: {time.ctime()}"
            }
        ]
    }
    # Сохраняем и применяем
    with open(MANIFEST_FILE, 'w') as f:
        json.dump(response_manifest, f)
    result = apply_update()
    return jsonify({"status": "ok", "message": result})

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "alive"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
