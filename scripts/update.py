#!/usr/bin/env python3
"""Prepare a candidate lock update, never promote or deploy it."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import urllib.request

root = Path(__file__).resolve().parents[1]
path = root / 'deps.lock.json'
lock = json.loads(path.read_text())

def api(endpoint):
    return json.loads(subprocess.check_output(['gh', 'api', endpoint]))

def digest(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read(128 * 1024 * 1024 + 1)
    if len(data) > 128 * 1024 * 1024:
        raise ValueError('Candidate exceeds download limit')
    return hashlib.sha256(data).hexdigest()

relapse = lock['relapse']
commit = api('repos/' + relapse['repo'] + '/commits/main')['sha']
if commit != relapse['commit']:
    relapse['commit'] = commit
    relapse['url'] = 'https://codeload.github.com/' + relapse['repo'] + '/tar.gz/' + commit
    relapse['sha256'] = digest(relapse['url'])
for repo in sorted({item['repo'] for item in lock['assets']}):
    releases = api('repos/' + repo + '/releases?per_page=20')
    # New prereleases are reported by track.py but not automatically selected.
    release = next((item for item in releases if not item['draft'] and not item['prerelease']), None)
    pins = [item for item in lock['assets'] if item['repo'] == repo]
    if not release or release['tag_name'] == pins[0]['tag']:
        continue
    # Do not downgrade a deliberately reviewed prerelease to an older stable tag.
    current = next((item for item in releases if item['tag_name'] == pins[0]['tag']), None)
    if current and current['published_at'] > release['published_at']:
        continue
    for pin in pins:
        # A versioned asset name may change with the tag; ambiguity fails closed.
        pattern = re.escape(pin['name']).replace(re.escape(pin['tag']), '.+')
        matches = [asset for asset in release['assets'] if re.fullmatch(pattern, asset['name'])]
        if len(matches) != 1:
            raise ValueError('Manual asset review needed: ' + repo + ' ' + pin['id'])
        asset = matches[0]
        reported = asset.get('digest', '')
        if not re.fullmatch('sha256:[a-f0-9]{64}', reported):
            raise ValueError('Candidate has no GitHub digest')
        actual = digest(asset['browser_download_url'])
        if actual != reported[7:]:
            raise ValueError('Candidate asset digest mismatch')
        pin.update(tag=release['tag_name'], name=asset['name'], url=asset['browser_download_url'], sha256=actual)
old = json.loads(path.read_text())
if lock != old:
    lock.pop('sources', None)
    lock['hardware'] = 'UNKNOWN: new candidate; hardware acceptance is required before promotion'
    path.write_text(json.dumps(lock, indent=2) + '\n')
    subprocess.run(['python3', str(root / 'scripts' / 'pin_sources.py')], check=True)
    print('Prepared a candidate; no stable files changed or deployed.')
else:
    print('No automatic candidate change; see track.py for prereleases and same-tag mutations.')
