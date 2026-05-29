# setup_secrets.py
from utils.secrets_manager import SecretsManager
import sys

sm = SecretsManager()
token = input('Enter GitHub token (или Enter для пропуска): ').strip()
if token:
    secrets = sm.load()
    secrets['github_token'] = token
    sm.save(secrets)
    print('[✔] GitHub token saved encrypted')
else:
    print('[!] No token provided — push будет пропущен')