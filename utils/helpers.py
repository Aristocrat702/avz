import socket, json, os

SETTINGS_FILE = "avz_settings.json"
PROFILES_FILE = "attack_profiles.json"

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    return {"theme": "dark"}

def save_settings(s):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(s, f, indent=2)

def load_profiles():
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE) as f:
            return json.load(f)
    return {}

def save_profile(name, config):
    profiles = load_profiles()
    profiles[name] = config
    with open(PROFILES_FILE, 'w') as f:
        json.dump(profiles, f, indent=2)

def delete_profile(name):
    profiles = load_profiles()
    if name in profiles:
        del profiles[name]
        with open(PROFILES_FILE, 'w') as f:
            json.dump(profiles, f, indent=2)