#!/usr/bin/env python3
"""Assemble a candidate payload tree from the committed pins and the served tree.

Run it from a stage directory that holds ``new/`` (a copy of the tree currently
served) and ``inputs/`` (the download cache keyed by SHA-256)::

    cd /home/billz/myfl-stage-YYYYMMDD
    python3 <repo>/scripts/assemble.py [PREVIOUS_TREE]

``PREVIOUS_TREE`` defaults to ``/opt/ps5-host/site``. Pins come from the locks in
this repository, so a rebuild only needs the previous tree and the commit. The
script verifies the previous tree against its own receipt, reuses any input whose
bytes already hash to the pin, downloads and hashes the rest, swaps changed
payloads in every served folder, patches ``index.html`` and ``payloads.json``,
rebuilds ``autoloader.zip`` and rewrites ``manifest.json`` and ``SHA256SUMS``.
Published files are never deleted, and nothing is written outside the stage.
"""
import concurrent.futures
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORK = pathlib.Path.cwd()
OLD = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '/opt/ps5-host/site').resolve()
OUT = WORK / 'new'
CACHE = WORK / 'inputs'
CATALOGUE_ORIGIN = 'https://exploit.myfl.uk/relapse/payloads/'
PAYLOAD_FOLDERS = ('relapse/payloads', 'managed/payloads', 'autoloader/ps5_autoloader')
APPROVED_HOSTS = ('https://github.com/', 'https://codeload.github.com/',
                  'https://www.bearssl.org/gitweb/', 'https://exploit.myfl.uk/downloads/',
                  'https://exploit.myfl.uk/sources/')

sys.path.insert(0, str(ROOT / 'scripts'))
from build import check_elf, served_name


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_receipt(tree):
    for line in (tree / 'SHA256SUMS').read_text().splitlines():
        sha, name = line.split('  ', 1)
        assert digest(tree / name) == sha, tree / name


def cached(item):
    for candidate in (CACHE / item['sha256'], OUT / 'sources' / item['name'],
                      OUT / 'downloads' / item['name'], WORK / item['name']):
        if candidate.is_file() and digest(candidate) == item['sha256']:
            return candidate
    return None


def fetch(item):
    hit = cached(item)
    if hit:
        return hit
    if not item['url'].startswith(APPROVED_HOSTS):
        raise SystemExit('pinned input host is not approved: ' + item['url'])
    print('Downloading', item['name'], flush=True)
    subprocess.run(['curl', '-fLsS', '--retry', '3', '--connect-timeout', '20',
                    '--max-time', '600', item['url'], '-o', str(CACHE / item['sha256'])],
                   check=True)
    target = CACHE / item['sha256']
    # The pin, not the release page, decides what is accepted.
    assert digest(target) == item['sha256'], item['name']
    return target


def main():
    if not OUT.is_dir():
        raise SystemExit('stage is missing new/: copy the served tree there first')
    verify_receipt(OLD)
    manifest = json.loads((ROOT / 'deps.lock.json').read_text())
    manifest['orbit'] = json.loads((ROOT / 'orbit.lock.json').read_text())
    manifest['prosperostore'] = json.loads((ROOT / 'prosperostore.lock.json').read_text())
    previous = json.loads((OLD / 'manifest.json').read_text())
    assets = (manifest['assets'] + manifest['orbit']['assets']
              + [manifest['orbit']['tv_app'], manifest['prosperostore']['asset']])
    sources = (manifest['sources'] + manifest['orbit']['sources']
               + manifest['prosperostore']['sources'])
    CACHE.mkdir(exist_ok=True)
    work = [('asset', item) for item in assets] + [('source', item) for item in sources]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        files = list(pool.map(lambda pair: fetch(pair[1]), work))

    changed = []
    for (kind, item), path in zip(work, files):
        if kind == 'source':
            target = OUT / 'sources' / item['name']
            if path != target:
                shutil.copyfile(path, target)
            continue
        dest = OUT / 'downloads' / item['name']
        if path != dest:
            shutil.copyfile(path, dest)
        if item['name'].endswith('.elf'):
            check_elf(path.read_bytes())
            stable = OUT / 'downloads' / served_name(item)
            if stable != dest:
                # Keep the name the runtime and catalogue use downloadable too.
                shutil.copyfile(path, stable)
            for folder in PAYLOAD_FOLDERS:
                target = OUT / folder / served_name(item)
                if target.exists() or (item.get('id') == 'autoloader-installer'
                                       and folder != 'autoloader/ps5_autoloader'):
                    shutil.copyfile(path, target)
        if item.get('id', '').startswith('orbit-'):
            # Keep the versioned input URL available after rebuilding.
            versioned = item['url'].rsplit('/', 1)[-1]
            if dest.name != versioned:
                shutil.copyfile(path, OUT / 'downloads' / versioned)
        before = next((pin for pin in
                       previous['assets'] + previous['orbit']['assets']
                       + [previous['orbit']['tv_app'], previous['prosperostore']['asset']]
                       if pin.get('id') == item.get('id')), None)
        if before and before['sha256'] != item['sha256']:
            changed.append((before, item))

    page = (OUT / 'index.html').read_text()
    for before, item in changed:
        old_url = 'https://github.com/' + before['repo'] + '/releases/tag/' + before['tag']
        new_url = item.get('instructions') or ('https://github.com/' + item['repo']
                                               + '/releases/tag/' + item['tag'])
        page = page.replace(old_url, new_url)
        page = page.replace(before['name'], served_name(item)).replace(before['tag'], item['tag'])
    page = page.replace(previous['orbit']['tv_app']['version'],
                        manifest['orbit']['tv_app']['version'])
    page = page.replace(previous['orbit']['assets'][0]['tag'][1:],
                        manifest['orbit']['assets'][0]['tag'][1:])
    page = page.replace(previous['orbit']['sources'][0]['name'],
                        manifest['orbit']['sources'][0]['name'])
    (OUT / 'index.html').write_text(page)

    catalogue = json.loads((OUT / 'payloads.json').read_text())
    for entry in catalogue['payloads']:
        for before, item in changed:
            # A changed asset moves version, checksum and the served filename
            # together; leaving the old filename behind makes Payload Manager
            # download one file and check it against another version's digest.
            if entry['checksum'] == before['sha256'] or entry['filename'] == before['name']:
                entry.update(version=item['tag'], checksum=item['sha256'],
                             filename=served_name(item),
                             url=CATALOGUE_ORIGIN + served_name(item))
    (OUT / 'payloads.json').write_text(json.dumps(catalogue, indent=2) + '\n')
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')

    with zipfile.ZipFile(OUT / 'autoloader.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for file in sorted((OUT / 'autoloader').rglob('*')):
            if file.is_file():
                entry = zipfile.ZipInfo(str(file.relative_to(OUT / 'autoloader')),
                                        (1980, 1, 1, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(entry, file.read_bytes())

    (OUT / 'SHA256SUMS').write_text(''.join(
        digest(path) + '  ' + str(path.relative_to(OUT)) + '\n'
        for path in sorted(OUT.rglob('*')) if path.is_file() and path.name != 'SHA256SUMS'))
    (WORK / 'changes.json').write_text(json.dumps(changed, indent=2) + '\n')
    print('Assembled', len(list(OUT.rglob('*'))), 'entries; changes',
          [(item['id'], item['tag']) for _, item in changed], flush=True)


if __name__ == '__main__':
    main()
