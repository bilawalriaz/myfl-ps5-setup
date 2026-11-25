#!/usr/bin/env python3
"""Validate the tree assembled by ``assemble.py`` and write the final receipt.

Run from the same stage directory, after ``assemble.py``::

    cd /home/billz/myfl-stage-YYYYMMDD
    python3 <repo>/scripts/finalize.py [PREVIOUS_TREE]

It installs ``THIRD_PARTY.md`` from the repository, proves the launcher and the
managed-entry sources are untouched, re-hashes every pinned asset and source
archive, re-checks every ELF, proves every Payload Manager catalogue entry hashes
to its claimed checksum against the served bytes, proves ``autoloader.zip``
carries the same bytes as ``autoloader/``, rejects symlinks and paths that leave
the tree, and rewrites ``SHA256SUMS`` to cover every file except itself.
"""
import hashlib
import json
import pathlib
import shutil
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORK = pathlib.Path.cwd()
OLD = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '/opt/ps5-host/site').resolve()
OUT = WORK / 'new'

sys.path.insert(0, str(ROOT / 'scripts'))
from build import check_elf, served_name


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    shutil.copyfile(ROOT / 'THIRD_PARTY.md', OUT / 'THIRD_PARTY.md')

    # The launcher and the managed-entry page are copies of the previous tree.
    for folder in ('start', 'managed/src'):
        for path in (OLD / folder).rglob('*'):
            if path.is_file():
                assert (OUT / path.relative_to(OLD)).read_bytes() == path.read_bytes(), path

    manifest = json.loads((OUT / 'manifest.json').read_text())
    assets = (manifest['assets'] + manifest['orbit']['assets']
              + [manifest['orbit']['tv_app'], manifest['prosperostore']['asset']])
    for item in assets:
        path = OUT / 'downloads' / item['name']
        assert digest(path) == item['sha256'], path
        if item['name'].endswith('.elf'):
            check_elf(path.read_bytes())
            name = served_name(item)
            for folder in ('managed/payloads', 'relapse/payloads', 'autoloader/ps5_autoloader'):
                copy = OUT / folder / name
                if copy.exists():
                    assert copy.read_bytes() == path.read_bytes(), copy
    for item in (manifest['sources'] + manifest['orbit']['sources']
                 + manifest['prosperostore']['sources']):
        assert digest(OUT / 'sources' / item['name']) == item['sha256'], item['name']

    # Payload Manager refuses a source entry when the file it names does not
    # hash to the checksum it publishes, so check the catalogue, not the manifest.
    catalogue = json.loads((OUT / 'payloads.json').read_text())
    assert catalogue['payloads'], 'empty catalogue'
    for entry in catalogue['payloads']:
        path = OUT / 'relapse' / 'payloads' / entry['filename']
        assert path.is_file(), 'catalogue names a missing file: ' + entry['filename']
        assert digest(path) == entry['checksum'], 'catalogue checksum mismatch: ' + entry['filename']
        assert entry['url'].endswith('/relapse/payloads/' + entry['filename']), entry['url']

    # Nothing may escape the tree or be a link.
    for path in OUT.rglob('*'):
        assert not path.is_symlink(), path
        if path.is_file():
            assert path.resolve().is_relative_to(OUT.resolve()), path
            assert '..' not in path.parts, path

    with zipfile.ZipFile(OUT / 'autoloader.zip') as archive:
        names = [name for name in archive.namelist() if not name.endswith('/')]
        assert sorted(names) == sorted(str(p.relative_to(OUT / 'autoloader'))
                                       for p in (OUT / 'autoloader').rglob('*') if p.is_file())
        for name in names:
            assert archive.read(name) == (OUT / 'autoloader' / name).read_bytes(), name

    autoload = (OUT / 'autoloader' / 'ps5_autoloader' / 'autoload.txt').read_text()
    assert autoload == (OLD / 'autoloader/ps5_autoloader/autoload.txt').read_text(), \
        'autoload.txt changed'

    (OUT / 'SHA256SUMS').write_text(''.join(
        digest(path) + '  ' + str(path.relative_to(OUT)) + '\n'
        for path in sorted(OUT.rglob('*')) if path.is_file() and path.name != 'SHA256SUMS'))
    print('Validated payloads, source archives, catalogue, ZIP, autoload.txt and tree bounds')
    print('catalogue entries', len(catalogue['payloads']))
    print('receipt', digest(OUT / 'SHA256SUMS'))


if __name__ == '__main__':
    main()
