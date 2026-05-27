import socket
import requests
import ssl
from utils.logger import log

class TargetAnalyzer:
    def __init__(self, target):
        self.target = target
        self.open_ports = []
        self.http_headers = {}
        self.ssl_info = {}

    def quick_scan(self):
        """Быстрое сканирование портов"""
        common_ports = [21,22,25,53,80,110,143,443,993,995,3306,3389,8080]
        for port in common_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((self.target, port))
            if result == 0:
                self.open_ports.append(port)
            sock.close()
        log(f"[Analyzer] Открытые порты: {self.open_ports}")

    def check_http(self):
        """Получение HTTP заголовков"""
        try:
            resp = requests.head(f"http://{self.target}", timeout=5)
            self.http_headers = dict(resp.headers)
            log(f"[Analyzer] HTTP заголовки: {self.http_headers}")
        except Exception as e:
            log(f"[Analyzer] HTTP ошибка: {e}")

    def check_ssl(self):
        """Получение информации о SSL сертификате"""
        try:
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=self.target) as s:
                s.settimeout(3)
                s.connect((self.target, 443))
                cert = s.getpeercert()
                self.ssl_info = cert
        except Exception as e:
            log(f"[Analyzer] SSL ошибка: {e}")

    def recommend(self):
        """На основе собранных данных выдаёт рекомендацию по вектору атаки"""
        self.quick_scan()
        self.check_http()
        self.check_ssl()

        if 80 in self.open_ports and 'Server' in self.http_headers:
            server = self.http_headers.get('Server', '').lower()
            if 'apache' in server:
                return "multivector", "Apache обнаружен, оптимально комбо SYN + HTTP флуд"
            elif 'nginx' in server:
                return "tls_exhaustion", "Nginx уязвим к TLS перегрузке"
        if 443 in self.open_ports:
            return "multivector", "Открыт HTTPS, эффективен Multivector Burst"
        if 53 in self.open_ports:
            return "dns_amp", "Открыт DNS, возможна амплификация"
        if 22 in self.open_ports:
            return "tcp", "SSH открыт, можно TCP флуд"
        return "syn", "Стандартный SYN флуд"
