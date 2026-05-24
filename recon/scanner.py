import socket, requests, cloudscraper, dns.resolver, whois, time, threading, json, re, subprocess, os, ssl, hashlib, base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from wappalyzer import Wappalyzer
from urllib.parse import urlparse

# Необязательный модуль для favicon
try:
    import mmh3
    MMH3_AVAILABLE = True
except ImportError:
    MMH3_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

SHODAN_DB_URL = "https://internetdb.shodan.io/{ip}"

class ReconScanner:
    def __init__(self, log_callback=None, progress_callback=None):
        self.log = log_callback or print
        self.progress = progress_callback
        self._stop_scan = False

    def _normalize(self, target):
        if not target.startswith(('http://', 'https://')):
            target = 'https://' + target
        parsed = urlparse(target)
        domain = parsed.netloc
        if not domain:
            domain = parsed.path
        return domain, target

    def full_report(self, target, scan_all_ports=False, use_nuclei=False, use_amass=False):
        self._stop_scan = False
        domain, url = self._normalize(target)
        report = {'target': domain, 'url': url}
        total_phases = 10
        phase = 0

        def advance(description):
            nonlocal phase
            phase += 1
            self.log(f"[{phase}/{total_phases}] {description}...\n")
            if self.progress:
                self.progress(phase / total_phases * 100)

        advance("IP и геолокация")
        self._add_network_info(domain, report)

        advance("Whois")
        self._add_whois(domain, report)

        advance("DNS-записи")
        self._add_dns_records(domain, report)

        advance("HTTP и заголовки")
        self._add_http_info(url, report)

        advance("Shodan InternetDB")
        self._add_shodan_info(domain, report)

        advance("SSL-сертификат")
        self._add_ssl_info(domain, report)

        advance("CMS и технологии")
        report['cms'] = self._detect_cms(domain)
        report['technologies'] = self._get_technologies(url)
        if MMH3_AVAILABLE:
            report['favicon_hash'] = self._get_favicon_hash(domain)
        else:
            report['favicon_hash'] = None

        advance("Скрытые пути")
        report['hidden_paths'] = self._find_hidden_paths(domain)

        advance("Поддомены (crt.sh)")
        report['subdomains'] = self._get_subdomains(domain)
        if use_amass:
            self.log("[*] Дополнительный поиск поддоменов через Amass...\n")
            report['subdomains'] = self._get_subdomains_amass(domain, report.get('subdomains', []))

        advance("Порты и уязвимости")
        if scan_all_ports:
            report['ports'] = self._scan_ports_all(domain)
        else:
            report['ports'] = self._scan_ports_common(domain)
        report['vuln'] = self._get_vuln_tests(url)
        server = report.get('http', {}).get('server', '')
        report['cve'] = self._get_cve(server)
        if use_nuclei:
            report['nuclei'] = self._run_nuclei(domain)
        else:
            report['nuclei'] = []
        if self.progress:
            self.progress(100)

        self.log("[✓] Разведка завершена.\n")
        return report

    def _add_network_info(self, domain, report):
        try:
            answers = dns.resolver.resolve(domain, 'A')
            ips = [str(r) for r in answers]
            report['ips'] = ips
            if ips:
                report['ping'] = self._ping(ips[0])
                geo = requests.get(f'http://ip-api.com/json/{ips[0]}', timeout=3).json()
                report['geo'] = f"{geo.get('country','')} {geo.get('regionName','')} {geo.get('isp','')}"
                # Поиск реального IP (если домен за CDN)
                if len(ips) == 1 and geo.get('isp', '').lower() in ['cloudflare', 'akamai', 'fastly']:
                    real_ip = self._find_real_ip(domain)
                    if real_ip:
                        report['real_ip'] = real_ip
        except Exception as e:
            self.log(f"[!] DNS/Geo: {e}\n")
            report['ips'] = []

    def _add_whois(self, domain, report):
        try:
            w = whois.whois(domain)
            report['whois'] = w.text[:500] if w.text else "нет данных"
        except:
            report['whois'] = "неизвестно"

    def _add_dns_records(self, domain, report):
        dns_info = {}
        for rtype in ['MX', 'NS', 'TXT']:
            try:
                answers = dns.resolver.resolve(domain, rtype)
                dns_info[rtype] = [str(r) for r in answers]
            except:
                dns_info[rtype] = []
        report['dns'] = dns_info

    def _add_http_info(self, url, report):
        info = {}
        try:
            scraper = cloudscraper.create_scraper()
            r = scraper.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
            info['server'] = r.headers.get('Server', 'не указан')
            info['cloudflare'] = 'cloudflare' in r.text.lower()
            # Заголовки безопасности
            security_headers = ['Strict-Transport-Security', 'Content-Security-Policy', 'X-Frame-Options', 'X-Content-Type-Options']
            info['security_headers'] = {h: r.headers.get(h, 'отсутствует') for h in security_headers}
            # Поиск email
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
            info['emails'] = list(set(emails))[:10]
            for fname in ['robots.txt', 'sitemap.xml']:
                try:
                    full_url = url.rstrip('/') + '/' + fname
                    rr = requests.get(full_url, timeout=3)
                    info[fname] = rr.text[:300] if rr.status_code==200 else f"HTTP {rr.status_code}"
                except:
                    info[fname] = "ошибка"
        except:
            info = {'server': 'неизвестен', 'cloudflare': False, 'security_headers': {}, 'emails': []}
        report['http'] = info

    def _add_shodan_info(self, domain, report):
        if not report.get('ips'):
            return
        try:
            ip = report['ips'][0]
            resp = requests.get(SHODAN_DB_URL.format(ip=ip), timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                report['shodan'] = {
                    'ports': data.get('ports', []),
                    'vulns': data.get('vulns', []),
                    'tags': data.get('tags', [])
                }
        except:
            pass

    def _add_ssl_info(self, domain, report):
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    report['ssl'] = {
                        'issuer': dict(x[0] for x in cert.get('issuer', [])),
                        'subject': dict(x[0] for x in cert.get('subject', [])),
                        'notBefore': cert.get('notBefore'),
                        'notAfter': cert.get('notAfter'),
                        'altNames': cert.get('subjectAltName', [])
                    }
        except:
            report['ssl'] = None

    def _detect_cms(self, domain):
        cms = ''
        try:
            r = requests.get(f'http://{domain}', timeout=5)
            html = r.text[:2000]
            if 'wp-content' in html or '/wp-json/' in html:
                cms = 'WordPress'
            elif 'Joomla' in html or 'joomla' in html:
                cms = 'Joomla'
            elif 'Drupal' in html:
                cms = 'Drupal'
            elif 'bitrix' in html:
                cms = '1C-Bitrix'
            elif 'opencart' in html:
                cms = 'OpenCart'
        except:
            pass
        return cms

    def _get_technologies(self, url):
        try:
            wapp = Wappalyzer()
            analysis = wapp.analyze_with_requests(url)
            return list(analysis.keys()) if analysis else []
        except:
            return []

    def _get_favicon_hash(self, domain):
        try:
            r = requests.get(f'http://{domain}/favicon.ico', timeout=5)
            if r.status_code == 200:
                favicon = r.content
                b64 = base64.b64encode(favicon)
                hash = mmh3.hash(b64)
                return hash
        except:
            return None

    def _find_hidden_paths(self, domain):
        paths = ['/wp-json/wp/v2/users', '/admin', '/phpmyadmin', '/api', '/graphql', '/.git/HEAD', '/.env']
        found = []
        for path in paths:
            try:
                r = requests.get(f'http://{domain}{path}', timeout=3)
                if r.status_code != 404:
                    found.append(path)
            except:
                pass
        return found

    def _find_real_ip(self, domain):
        try:
            # Используем SecurityTrails бесплатный API
            url = f"https://securitytrails.com/api/v1/history/{domain}/dns/a"
            headers = {'APIKEY': 'free-api-key'}  # нужен ключ
            # Заглушка: попробуем получить старый A через crt.sh
            return None
        except:
            return None

    def _get_subdomains(self, domain):
        subdomains = []
        try:
            url = f"https://crt.sh/?q=%25.{domain}&output=json"
            for attempt in range(2):
                try:
                    resp = requests.get(url, timeout=20)
                    if resp.status_code == 200:
                        data = resp.json()
                        for entry in data:
                            name = entry.get('name_value', '')
                            for n in name.split('\n'):
                                n = n.strip().lower()
                                if n not in subdomains and '*' not in n and n.endswith('.' + domain):
                                    subdomains.append(n)
                        break
                except requests.exceptions.ReadTimeout:
                    self.log(f"[!] crt.sh таймаут, попытка {attempt+1}/2\n")
        except Exception as e:
            self.log(f"[!] Ошибка crt.sh: {e}\n")
        return list(set(subdomains))[:50]

    def _get_subdomains_amass(self, domain, existing):
        try:
            proc = subprocess.run(['amass', 'enum', '-d', domain, '-o', 'amass_tmp.txt'],
                                  timeout=120, capture_output=True, text=True)
            if proc.returncode == 0 and os.path.exists('amass_tmp.txt'):
                with open('amass_tmp.txt') as f:
                    for line in f:
                        sub = line.strip().lower()
                        if sub not in existing and sub.endswith('.' + domain):
                            existing.append(sub)
                os.remove('amass_tmp.txt')
        except Exception as e:
            self.log(f"[!] Ошибка Amass: {e}\n")
        return existing

    def _get_cve(self, server_header):
        cve_list = []
        if not server_header or server_header == 'не указан':
            return cve_list
        try:
            match = re.search(r'([A-Za-z]+)/([\d.]+)', server_header)
            if match:
                software = match.group(1).lower()
                version = match.group(2)
                query = f"{software} {version}"
                url = "https://vulners.com/api/v3/search/lucene/"
                resp = requests.post(url, json={"query": query, "size": 5}, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    for doc in data.get('data', {}).get('search', []):
                        cve_list.append({
                            'id': doc.get('id', ''),
                            'title': doc.get('title', ''),
                            'cvss': doc.get('cvss', {}).get('score', 'N/A')
                        })
        except:
            pass
        return cve_list

    def _run_nuclei(self, domain):
        results = []
        try:
            proc = subprocess.run(['nuclei', '-target', domain, '-silent', '-json'],
                                  timeout=120, capture_output=True, text=True)
            if proc.returncode == 0 and proc.stdout:
                for line in proc.stdout.splitlines():
                    try:
                        data = json.loads(line)
                        results.append({
                            'template': data.get('template-id', ''),
                            'name': data.get('info', {}).get('name', ''),
                            'severity': data.get('info', {}).get('severity', ''),
                            'matched': data.get('matched-at', '')
                        })
                    except:
                        pass
        except:
            pass
        return results

    def _get_vuln_tests(self, url):
        return {
            'sqli': self._test_sqli(url),
            'xss': self._test_xss(url)
        }

    def _test_sqli(self, url):
        for p in ["'", '"', "1' OR '1'='1"]:
            try:
                if 'sql' in requests.get(url+"?id="+p, timeout=3).text.lower():
                    return True
            except:
                pass
        return False

    def _test_xss(self, url):
        p = "<script>alert(1)</script>"
        try:
            if p in requests.get(url+"?q="+p, timeout=3).text:
                return True
        except:
            pass
        return False

    def _scan_ports_common(self, host):
        return self._scan_port_range(host, 1, 1024)

    def _scan_ports_all(self, host):
        return self._scan_port_range(host, 1, 65535)

    def _scan_port_range(self, host, start, end):
        open_ports = []
        self.log(f"Сканирование портов {start}-{end}...\n")
        with ThreadPoolExecutor(max_workers=80) as ex:
            futures = {ex.submit(self._check_port, host, port): port for port in range(start, end+1)}
            for f in as_completed(futures):
                if self._stop_scan:
                    break
                port = futures[f]
                if f.result():
                    open_ports.append(port)
        return open_ports

    def _check_port(self, host, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            result = s.connect_ex((host, port))
            s.close()
            return result == 0
        except:
            return False

    def _ping(self, host):
        try:
            import ping3
            t = ping3.ping(host, timeout=2)
            return f"{int(t*1000)} мс" if t else "нет ответа"
        except:
            return "ошибка"

    def stop(self):
        self._stop_scan = True

    def export_pdf(self, report, filename):
        if not PDF_AVAILABLE:
            self.log("[!] reportlab не установлен. Установите: pip install reportlab\n")
            return
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph(f"<b>Отчёт разведки: {report.get('target','')}</b>", styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"IP: {', '.join(report.get('ips', []))}", styles['Normal']))
        story.append(Paragraph(f"Geo: {report.get('geo')}", styles['Normal']))
        story.append(Paragraph(f"Пинг: {report.get('ping')}", styles['Normal']))
        story.append(Paragraph(f"Whois: {report.get('whois')}", styles['Normal']))
        http = report.get('http', {})
        story.append(Paragraph(f"Сервер: {http.get('server')}", styles['Normal']))
        story.append(Paragraph(f"Cloudflare: {http.get('cloudflare')}", styles['Normal']))
        story.append(Paragraph(f"robots.txt: {http.get('robots.txt')}", styles['Normal']))
        story.append(Paragraph(f"sitemap.xml: {http.get('sitemap.xml')}", styles['Normal']))
        subs = report.get('subdomains', [])
        story.append(Paragraph(f"Поддомены ({len(subs)}): {', '.join(subs)}", styles['Normal']))
        techs = report.get('technologies', [])
        story.append(Paragraph(f"Технологии: {', '.join(techs)}", styles['Normal']))
        cve_list = report.get('cve', [])
        if cve_list:
            story.append(Paragraph("<b>Найденные CVE:</b>", styles['Heading2']))
            for cve in cve_list:
                story.append(Paragraph(f"{cve['id']}: {cve['title']} (CVSS {cve['cvss']})", styles['Normal']))
        nuclei = report.get('nuclei', [])
        if nuclei:
            story.append(Paragraph("<b>Nuclei результаты:</b>", styles['Heading2']))
            for n in nuclei:
                story.append(Paragraph(f"{n['template']}: {n['name']} ({n['severity']})", styles['Normal']))
        vuln = report.get('vuln', {})
        story.append(Paragraph(f"SQLi: {vuln.get('sqli')}", styles['Normal']))
        story.append(Paragraph(f"XSS: {vuln.get('xss')}", styles['Normal']))
        ports = report.get('ports', [])
        story.append(Paragraph(f"Открытые порты: {', '.join(map(str, ports))}", styles['Normal']))
        doc.build(story)
        self.log(f"[PDF] Отчёт сохранён в {filename}\n")