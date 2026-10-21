#!/usr/bin/env python3
"""Render the User's Guide start page from the pinned payload list.

The guide origin is a plain HTTPS page without the exploit's module support, so
this stays a classic document with no external assets. It only builds a link:
Relapse runs after the console follows that link, never on page load.
"""
import argparse
import json
from pathlib import Path

from managed_entry import LABELS, LINUX_WARNINGS, PAYLOADS, PROFILES

ROOT = Path(__file__).resolve().parents[1]


def render(origin=''):
    """Return the start page; `origin` prefixes the exploit link when the guide
    page is served by a host that cannot serve /managed/ itself."""
    items = [{'file': name, 'label': LABELS.get(name, name), 'warning': LINUX_WARNINGS.get(name)}
             for name in PAYLOADS]
    page = (ROOT / 'start.html').read_text()
    page = page.replace('__PAYLOADS__', json.dumps(items, indent=2))
    page = page.replace('__PROFILES__', json.dumps(PROFILES))
    page = page.replace('__ORIGIN__', json.dumps(origin))
    if '__' in page.split('<script>', 1)[1]:
        raise ValueError('An unrendered placeholder remains in the start page')
    return page


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', default='',
                        help='Exploit origin, for example http://192.168.1.152 when the guide page is served alone')
    parser.add_argument('--output', required=True, help='File to write')
    arguments = parser.parse_args()
    target = Path(arguments.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render(arguments.origin))
    print('Wrote ' + str(target))


if __name__ == '__main__':
    main()
