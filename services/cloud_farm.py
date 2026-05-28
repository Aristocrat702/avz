import os, json, time
from utils.logger import log

try:
    from digitalocean import Manager as DOManager, Droplet
except: pass
try:
    from linode_api4 import LinodeClient
except: pass
try:
    from vultr import Vultr
except: pass

class CloudFarm:
    def __init__(self, config_file="cloud_config.json"):
        self.config = {}
        if os.path.exists(config_file):
            with open(config_file) as f:
                self.config = json.load(f)

    def deploy_if_needed(self, current_bot_count, min_bots=50):
        if current_bot_count < min_bots:
            needed = min_bots - current_bot_count
            log(f"[CloudFarm] Ботов {current_bot_count}, нужно {needed}, запускаю деплой")
            self.deploy(max(needed, 2))

    def deploy(self, count=2):
        if self.config.get('digitalocean', {}).get('enabled'):
            self._deploy_do(count)
        if self.config.get('linode', {}).get('enabled'):
            self._deploy_linode(count)
        if self.config.get('vultr', {}).get('enabled'):
            self._deploy_vultr(count)

    def _deploy_do(self, count):
        try:
            token = self.config['digitalocean']['token']
            manager = DOManager(token=token)
            for _ in range(count):
                droplet = Droplet(token=token,
                                  name=f'bot-{int(time.time())}',
                                  region='nyc3',
                                  image='ubuntu-20-04-x64',
                                  size_slug='s-1vcpu-1gb')
                droplet.create()
                log(f"[CloudFarm] DigitalOcean дроплет создан: {droplet.id}")
        except Exception as e:
            log(f"[CloudFarm] DO ошибка: {e}")

    def _deploy_linode(self, count):
        try:
            token = self.config['linode']['token']
            client = LinodeClient(token)
            for _ in range(count):
                client.linode.instance_create('g6-nanode-1', 'us-east', image='linode/ubuntu20.04', label=f'bot-{int(time.time())}')
                log("[CloudFarm] Linode инстанс создан")
        except Exception as e:
            log(f"[CloudFarm] Linode ошибка: {e}")

    def _deploy_vultr(self, count):
        try:
            api_key = self.config['vultr']['api_key']
            client = Vultr(api_key)
            for _ in range(count):
                client.server.create(dcid='1', vpsplanid='201', osid='215')
                log("[CloudFarm] Vultr сервер создан")
        except Exception as e:
            log(f"[CloudFarm] Vultr ошибка: {e}")
