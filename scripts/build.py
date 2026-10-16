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
MAX_DOWNLOAD = 384 * 1024 * 1024  # Orbit release source bundle includes dependency sources.
MAX_ARCHIVE_EXPANSION = 128 * 1024 * 1024


def download(item):
    if not item['url'].startswith(('https://github.com/', 'https://codeload.github.com/', 'https://www.bearssl.org/gitweb/', 'https://exploit.myfl.uk/downloads/', 'https://exploit.myfl.uk/sources/')):
        raise ValueError('Only approved pinned input hosts are allowed')
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
            if total > MAX_ARCHIVE_EXPANSION:
                raise ValueError('Expanded archive exceeds size limit')
            dest = target.joinpath(*path.parts[1:])
            dest.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as source:
                dest.write_bytes(source.read())


def build():
    manifest = json.loads((ROOT / 'deps.lock.json').read_text())
    manifest['orbit'] = json.loads((ROOT / 'orbit.lock.json').read_text())
    manifest['prosperostore'] = json.loads((ROOT / 'prosperostore.lock.json').read_text())
    assets = manifest['assets'] + manifest['orbit']['assets'] + [manifest['orbit']['tv_app'], manifest['prosperostore']['asset']]
    destination = ROOT / 'dist'
    if destination.exists():
        raise SystemExit('dist exists; keep it for rollback or move it before building')
    with tempfile.TemporaryDirectory(prefix='myfl-candidate-', dir=ROOT) as temporary:
        output = Path(temporary) / 'dist'
        output.mkdir()
        relapse = manifest['relapse']
        extract(download(relapse), output / 'relapse', 'Relapse-Exploit-' + relapse['commit'])
        for item in assets:
            data = download(item)
            if item['name'].endswith('.elf'):
                check_elf(data)
            dest = output / 'downloads' / item['name']
            dest.parent.mkdir(exist_ok=True)
            dest.write_bytes(data)
            if item.get('id', '').startswith('orbit-'):
                # Keep the versioned input URL available after rebuilding this host.
                (output / 'downloads' / item['url'].rsplit('/', 1)[-1]).write_bytes(data)
            if item['name'].endswith('.elf'):
                # Curated, independently pinned extras share the upstream loader folder.
                name = 'pldmgr.elf' if item['id'] == 'payload-manager' else item['name']
                (output / 'relapse' / 'payloads' / name).write_bytes(data)
        host = next(item for item in manifest['assets'] if item['id'] == 'autoloader-transport-host')
        assemble(output, output / 'downloads' / host['name'])
        for payload in (output / 'relapse' / 'payloads').glob('*.elf'):
            check_elf(payload.read_bytes())
        manual = output / 'autoloader' / 'ps5_autoloader'
        manual.mkdir(parents=True)
        for item in assets:
            if item.get('id') in ('kstuff', 'shadowmount', 'klog', 'ftp', 'payload-manager', 'orbit-torbox', 'onionhen'):
                shutil.copyfile(output / 'downloads' / item['name'], manual / ('pldmgr.elf' if item['id'] == 'payload-manager' else item['name']))
        (manual / 'autoload.txt').write_text('\n'.join(PAYLOADS) + '\n')
        (output / 'autoloader' / 'README.txt').write_text(
            'Launch after full boot.\n'
            'Copy ps5_autoloader to the USB root or /data/.\n'
            'The list starts logs, kstuff, ShadowMountPlus, FTP, Orbit TorBox and OnionHEN.\n'
            'The installer and local payload files are updated separately.\n')
        with zipfile.ZipFile(output / 'autoloader.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
            for file in sorted((output / 'autoloader').rglob('*')):
                if file.is_file():
                    entry = zipfile.ZipInfo(str(file.relative_to(output / 'autoloader')), (1980, 1, 1, 0, 0, 0))
                    entry.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(entry, file.read_bytes())
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        page = (ROOT / 'landing.html').read_text()
        titles = {'onionhen': 'OnionHEN', 'autoloader-installer': 'WebKit Autoloader installer', 'payload-manager': 'Payload Manager', 'kstuff': 'kstuff-lite', 'shadowmount': 'ShadowMountPlus', 'klog': 'Kernel log server', 'ftp': 'FTP server', 'orbit-upstream': 'Orbit Store (upstream)', 'orbit-torbox': 'Orbit Store with TorBox', 'autoloader-preview-installer': 'WebKit Autoloader installer (prerelease)'}
        catalogue = {'name': 'myfl.uk PS5 essentials', 'payloads': []}
        for item in assets:
            if item.get('id') in titles:
                name = 'pldmgr.elf' if item['id'] == 'payload-manager' else item['name']
                catalogue['payloads'].append({'name': titles[item['id']], 'filename': name,
                    'url': 'https://exploit.myfl.uk/relapse/payloads/' + name,
                    'version': item['tag'], 'checksum': item['sha256'],
                    'category': 'Setup' if item['id'] == 'autoloader-installer' else 'Essentials'})
        (output / 'payloads.json').write_text(json.dumps(catalogue, indent=2) + '\n')
        links = []
        for item in assets:
            if item.get('id') in titles:
                name = 'pldmgr.elf' if item['id'] == 'payload-manager' else item['name']
                instructions = ('/sources/' + manifest['orbit']['sources'][0]['name'] if item['id'] == 'orbit-torbox' else 'https://github.com/' + item['repo'] + '/releases/tag/' + html.escape(item['tag'], quote=True))
                links.append('<li><a href="/relapse/payloads/' + html.escape(name, quote=True) + '">' + html.escape(titles[item['id']] + ' ' + item['tag']) + '</a> - <a href="' + instructions + '">source / instructions</a></li>')
        begin, end = page.index('<ul>'), page.index('</ul>') + len('</ul>')
        prosperostore = manifest['prosperostore']['asset']
        links.append('<li><a href="/downloads/' + html.escape(prosperostore['name'], quote=True) + '">ProsperoStore ' + html.escape(prosperostore['tag']) + ' app ZIP</a> - extract PPSA99000 and copy it to /data/homebrew/PPSA99000; ShadowMountPlus registers it during its scan.</li>')
        eden = next(item for item in assets if item.get('id') == 'prosperoeden-app')
        links.append('<li><a href="/downloads/' + html.escape(eden['name'], quote=True) + '">ProsperoEden ' + html.escape(eden['tag']) + ' app ZIP</a> - copy its PPSA99008 folder to /data/homebrew/PPSA99008; ShadowMountPlus registers the app during its scan.</li>')
        links.append('<li><a href="/downloads/PPSA99177.ffpkg">Orbit Store TV app ' + html.escape(manifest['orbit']['tv_app']['version']) + '</a> - copy to /data/homebrew/ and let ShadowMountPlus register it.</li>')
        page = page[:begin] + '<ul>' + ''.join(links) + '</ul>' + page[end:]
        (output / 'index.html').write_text(page)
        source_dir = output / 'sources'
        source_dir.mkdir()
        for item in manifest.get('sources', []) + manifest['orbit']['sources'] + manifest['prosperostore']['sources']:
            (source_dir / item['name']).write_bytes(download(item))
        shutil.copyfile(ROOT / 'THIRD_PARTY.md', output / 'THIRD_PARTY.md')
        hashes = {str(path.relative_to(output)): hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in sorted(output.rglob('*')) if path.is_file()}
        (output / 'SHA256SUMS').write_text(''.join(f'{digest}  {name}\n' for name, digest in hashes.items()))
        shutil.move(str(output), destination)
    print('Built candidate in dist; no hardware, publication or deployment performed.')


if __name__ == '__main__':
    build()
