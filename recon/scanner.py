import socket
import dns.resolver
import requests
import whois
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import ssl

def scan_ports(host, ports=[22,80,443,8080]):
    open_ports = []
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        if result == 0:
            open_ports.append(port)
        sock.close()
    return open_ports

def dns_lookup(domain):
    records = {}
    for qtype in ['A', 'MX', 'NS', 'TXT']:
        try:
            answers = dns.resolver.resolve(domain, qtype)
            records[qtype] = [str(r) for r in answers]
        except:
            records[qtype] = []
    return records

def get_http_headers(url):
    try:
        resp = requests.head(url, timeout=5)
        return dict(resp.headers)
    except:
        return {}

def get_ssl_cert(host, port=443):
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=host) as s:
            s.connect((host, port))
            cert = s.getpeercert(binary_form=True)
            cert = x509.load_der_x509_certificate(cert, default_backend())
            return {
                'subject': cert.subject.rfc4514_string(),
                'issuer': cert.issuer.rfc4514_string(),
                'not_valid_before': cert.not_valid_before.isoformat(),
                'not_valid_after': cert.not_valid_after.isoformat()
            }
    except Exception as e:
        return {'error': str(e)}

def whois_lookup(domain):
    try:
        return whois.whois(domain)
    except:
        return {}
