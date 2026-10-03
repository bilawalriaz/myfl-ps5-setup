#!/usr/bin/env python3
"""Record source archives for reviewed release tags and their pinned submodules."""
import configparser
import hashlib
import json
from pathlib import Path
import re
import subprocess
import urllib.request

root = Path(__file__).resolve().parents[1]
path = root / 'deps.lock.json'
lock = json.loads(path.read_text())
seen = set()
records = []

def api(endpoint):
    return json.loads(subprocess.check_output(['gh', 'api', endpoint]))

def pin(repo, revision):
    commit = api('repos/' + repo + '/commits/' + revision)['sha']
    if (repo, commit) in seen:
        return
    seen.add((repo, commit))
    url = 'https://codeload.github.com/' + repo + '/tar.gz/' + commit
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read(128 * 1024 * 1024 + 1)
    if len(data) > 128 * 1024 * 1024:
        raise ValueError('Source exceeds bound')
    records.append({'repo': repo, 'commit': commit, 'url': url,
                    'name': repo.replace('/', '-') + '-' + commit[:12] + '.tar.gz',
                    'sha256': hashlib.sha256(data).hexdigest()})
    tree = api('repos/' + repo + '/git/trees/' + commit + '?recursive=1')['tree']
    links = {item['path']: item['sha'] for item in tree if item['type'] == 'commit'}
    if not links:
        return
    modules = subprocess.check_output(['gh', 'api', 'repos/' + repo + '/contents/.gitmodules?ref=' + commit,
                                      '-H', 'Accept: application/vnd.github.raw+json'], text=True)
    config = configparser.ConfigParser()
    config.read_string(modules)
    for section in config.sections():
        subpath, remote = config[section]['path'], config[section]['url']
        match = re.fullmatch(r'https://github.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?', remote)
        if remote == 'https://www.bearssl.org/git/BearSSL' and subpath in links:
            sha = links[subpath]
            url = 'https://www.bearssl.org/gitweb/?p=BearSSL;a=snapshot;h=' + sha + ';sf=tgz'
            with urllib.request.urlopen(url, timeout=60) as response:
                data = response.read(128 * 1024 * 1024 + 1)
            if len(data) > 128 * 1024 * 1024:
                raise ValueError('Source exceeds bound')
            records.append({'repo': 'BearSSL/BearSSL', 'commit': sha, 'url': url, 'name': 'BearSSL-' + sha[:12] + '.tar.gz', 'sha256': hashlib.sha256(data).hexdigest()})
            continue
        if not match or subpath not in links:
            raise ValueError('Unreviewed submodule origin: ' + repo + ' ' + subpath + ' ' + remote)
        pin(match[1], links[subpath])

for repo, revision in sorted({(item['repo'], item['tag']) for item in lock['assets']}):
    pin(repo, revision)
pin('ps5-payload-dev/sdk', 'f7fd02e6e195902a449b5e664917be8c01888b34')
lock['sources'] = records
path.write_text(json.dumps(lock, indent=2) + '\n')
print('Recorded', len(records), 'source archive pins; no payload was built or executed.')
