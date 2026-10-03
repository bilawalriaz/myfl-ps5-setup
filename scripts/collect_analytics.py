#!/usr/bin/env python3
"""Write private daily HTTP aggregates and DNS counters; collect no query history."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import urllib.request

root = Path(__file__).resolve().parents[1]
logs = subprocess.check_output(['docker', 'compose', '--project-directory', str(root / 'oracle'),
                               '-f', str(root / 'oracle' / 'compose.yaml'), 'logs',
                               '--since', '24h', '--no-log-prefix', '--no-color', 'web'])
web = json.loads(subprocess.check_output(['python3', str(root / 'scripts' / 'analytics.py')], input=logs))
address = subprocess.check_output(['docker', 'inspect', 'myfl-ps5-dns-1', '--format',
                                 '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'], text=True).strip()
with urllib.request.urlopen('http://' + address + ':9153/metrics', timeout=5) as response:
    metrics = response.read(1024 * 1024).decode()
dns = {}
for line in metrics.splitlines():
    match = re.match(r'coredns_dns_responses_total\{([^}]+)\} ([0-9.e+]+)', line)
    if match:
        code = re.search(r'rcode="([A-Z0-9]+)"', match[1])
        if code:
            dns[code[1]] = dns.get(code[1], 0) + float(match[2])
folder = Path('/var/lib/myfl-ps5-analytics')
folder.mkdir(exist_ok=True)
now = datetime.now(timezone.utc)
(folder / (now.strftime('%Y-%m-%d') + '.json')).write_text(json.dumps(
    {'captured': now.isoformat(), 'http_last_24h': web, 'dns_since_restart': dns}, indent=2) + '\n')
for file in folder.glob('*.json'):
    if now.timestamp() - file.stat().st_mtime > 7 * 86400:
        file.unlink()
print('Private request aggregates saved; no console success or unique-user claim.')
