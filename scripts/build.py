#!/usr/bin/env python3
"""Build an immutable candidate locally; never contact a console or deploy."""
import hashlib
import html
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import struct
import tarfile
import tempfile
import urllib.request
import zipfile
from managed_entry import assemble, PAYLOADS

ROOT = Path(__file__).resolve().parents[1]
MAX_DOWNLOAD = 128 * 1024 * 1024


def download(item):
    if not item['url'].startswith(('https://github.com/', 'https://codeload.github.com/', 'https://www.bearssl.org/gitweb/')):
        raise ValueError('Only pinned GitHub inputs are allowed')
    with urllib.request.urlopen(item['url'], timeout=60) as response:
        data = response.read(MAX_DOWNLOAD + 1)
    if len(data) > MAX_DOWNLOAD:
        raise ValueError('Download exceeds size limit')
    if hashlib.sha256(data).hexdigest() != item['sha256']:
        raise ValueError('SHA-256 mismatch: ' + item['url'])
    return data


def check_elf(data):
    # Section headers are required by elfldr framing; never strip the payload.
    if len(data) < 64 or data[:6] != b'\x7fELF\x02\x01':
        raise ValueError('Expected little-endian ELF64')
    if struct.unpack_from('<H', data, 18)[0] != 62:
        raise ValueError('Expected x86-64 PS5 payload')
    offset = struct.unpack_from('<Q', data, 40)[0]
    size, count = struct.unpack_from('<HH', data, 58)
    if not offset or size != 64 or not count or offset + size * count > len(data):
        raise ValueError('Missing or out-of-bounds ELF section headers')
    for index in range(count):
        section = offset + index * size
        kind = struct.unpack_from('<I', data, section + 4)[0]
        start, length = struct.unpack_from('<QQ', data, section + 24)
        if kind != 8 and start + length > len(data):
            raise ValueError('Out-of-bounds ELF section data')


def extract(data, target, prefix):
    total = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] != prefix:
                raise ValueError('Unsafe archive path')
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError('Archive links and special files are forbidden')
            total += member.size
            if total > MAX_DOWNLOAD:
                raise ValueError('Expanded archive exceeds size limit')
            dest = target.joinpath(*path.parts[1:])
            dest.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as source:
                dest.write_bytes(source.read())


def build():
    manifest = json.loads((ROOT / 'deps.lock.json').read_text())
    destination = ROOT / 'dist'
    if destination.exists():
        raise SystemExit('dist exists; keep it for rollback or move it before building')
    with tempfile.TemporaryDirectory(prefix='myfl-candidate-', dir=ROOT) as temporary:
        output = Path(temporary) / 'dist'
        output.mkdir()
        relapse = manifest['relapse']
        extract(download(relapse), output / 'relapse', 'Relapse-Exploit-' + relapse['commit'])
        for item in manifest['assets']:
            data = download(item)
            if item['name'].endswith('.elf'):
                check_elf(data)
            dest = output / 'downloads' / item['name']
            dest.parent.mkdir(exist_ok=True)
            dest.write_bytes(data)
            if item['name'].endswith('.elf'):
                # Curated, independently pinned extras share the upstream loader folder.
                name = 'pldmgr.elf' if item['id'] == 'payload-manager' else item['name']
                (output / 'relapse' / 'payloads' / name).write_bytes(data)
        host = next(item for item in manifest['assets'] if item['id'] == 'autoloader-host')
        assemble(output, output / 'downloads' / host['name'])
        for payload in (output / 'relapse' / 'payloads').glob('*.elf'):
            check_elf(payload.read_bytes())
        manual = output / 'autoloader' / 'ps5_autoloader'
        manual.mkdir(parents=True)
        for item in manifest['assets']:
            if item['id'] in ('kstuff', 'shadowmount', 'klog', 'ftp', 'payload-manager'):
                shutil.copyfile(output / 'downloads' / item['name'], manual / ('pldmgr.elf' if item['id'] == 'payload-manager' else item['name']))
        (manual / 'autoload.txt').write_text('\n'.join(PAYLOADS) + '\n')
        (output / 'autoloader' / 'README.txt').write_text(
            'Launch after full boot.\n'
            'Copy ps5_autoloader to the USB root or /data/.\n'
            'The list starts Payload Manager. Select extra services when needed.\n'
            'The installer and local payload files are updated separately.\n')
        with zipfile.ZipFile(output / 'autoloader.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
            for file in sorted((output / 'autoloader').rglob('*')):
                if file.is_file():
                    entry = zipfile.ZipInfo(str(file.relative_to(output / 'autoloader')), (1980, 1, 1, 0, 0, 0))
                    entry.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(entry, file.read_bytes())
        shutil.copyfile(ROOT / 'deps.lock.json', output / 'manifest.json')
        page = (ROOT / 'landing.html').read_text()
        titles = {'autoloader-installer': 'WebKit Autoloader installer', 'payload-manager': 'Payload Manager', 'kstuff': 'kstuff-lite', 'shadowmount': 'ShadowMountPlus', 'klog': 'Kernel log server', 'ftp': 'FTP server'}
        links = []
        for item in manifest['assets']:
            if item['id'] in titles:
                name = 'pldmgr.elf' if item['id'] == 'payload-manager' else item['name']
                links.append('<li><a href="/relapse/payloads/' + html.escape(name, quote=True) + '">' + html.escape(titles[item['id']] + ' ' + item['tag']) + '</a> — <a href="https://github.com/' + item['repo'] + '/releases/tag/' + html.escape(item['tag'], quote=True) + '">release instructions</a></li>')
        begin, end = page.index('<ul>'), page.index('</ul>') + len('</ul>')
        page = page[:begin] + '<ul>' + ''.join(links) + '</ul>' + page[end:]
        (output / 'index.html').write_text(page)
        source_dir = output / 'sources'
        source_dir.mkdir()
        for item in manifest.get('sources', []):
            (source_dir / item['name']).write_bytes(download(item))
        shutil.copyfile(ROOT / 'THIRD_PARTY.md', output / 'THIRD_PARTY.md')
        hashes = {str(path.relative_to(output)): hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in sorted(output.rglob('*')) if path.is_file()}
        (output / 'SHA256SUMS').write_text(''.join(f'{digest}  {name}\n' for name, digest in hashes.items()))
        shutil.move(str(output), destination)
    print('Built candidate in dist; no hardware, publication or deployment performed.')


if __name__ == '__main__':
    build()
