#!/usr/bin/env python3
"""Prepare an exact-name, non-recursive DNS review config for an explicit address."""
import argparse
import ipaddress
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--answer-ip', required=True, type=ipaddress.IPv4Address)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1] / '.cache' / 'dns'
root.mkdir(parents=True, exist_ok=True)
# Exact interception name comes from the pinned upstream PC host's DEFAULT_TARGET.
(root / 'Corefile').write_text('''manuals.playstation.net:1053 {
    file /etc/coredns/manuals.zone manuals.playstation.net
    prometheus 0.0.0.0:9153
    errors
}
.:1053 {
    template ANY ANY {
        rcode REFUSED
    }
    errors
}
''')
(root / 'manuals.zone').write_text(f'''$ORIGIN manuals.playstation.net.
$TTL 60
@ IN SOA ns.manuals.playstation.net. hostmaster.manuals.playstation.net. (2026100301 3600 600 86400 60)
@ IN NS ns.manuals.playstation.net.
@ IN A {args.answer_ip}
ns IN A {args.answer_ip}
''')
print('Prepared local DNS config; no listener or network change performed.')
