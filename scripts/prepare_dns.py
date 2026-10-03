#!/usr/bin/env python3
"""Prepare a PlayStation entry DNS config for an explicit address."""
import argparse
import ipaddress
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--answer-ip', required=True, type=ipaddress.IPv4Address)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1] / '.cache' / 'dns'
root.mkdir(parents=True, exist_ok=True)
# Exact interception name comes from the pinned upstream PC host's DEFAULT_TARGET.
zones = ['manuals.playstation.net', 'manuals.playstation.com']
blocks = []
for zone in zones:
    blocks.append(f"{zone}:1053 {{\n    file /etc/coredns/{zone}.zone {zone}\n    errors\n}}\n")
    (root / (zone + '.zone')).write_text(f"$ORIGIN {zone}.\n$TTL 60\n@ IN SOA ns.{zone}. hostmaster.{zone}. (2026100302 3600 600 86400 60)\n@ IN NS ns.{zone}.\n@ IN A {args.answer_ip}\nns IN A {args.answer_ip}\n")
blocks.append("""update.playstation.net:1053 {
    template ANY ANY {
        rcode NXDOMAIN
    }
    errors
}
.:1053 {
    prometheus 0.0.0.0:9153
    bufsize 512
    cache 60 {
        success 1024
        denial 1024
    }
    forward . 1.1.1.1 1.0.0.1 {
        force_tcp
        max_concurrent 32
        max_fails 0
    }
    errors
}
""")
(root / 'Corefile').write_text('\n'.join(blocks))
print('Prepared restricted DNS config; no listener or network change performed.')
