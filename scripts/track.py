#!/usr/bin/env python3
"""Report upstream drift; never update the reviewed lock or stable channel."""
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
lock = json.loads((root / 'deps.lock.json').read_text())

def api(endpoint):
    return json.loads(subprocess.check_output(['gh', 'api', endpoint], text=True))

rows = []
source = lock['relapse']
commit = api('repos/' + source['repo'] + '/commits/main')['sha']
rows.append({'repo': source['repo'], 'pinned': source['commit'], 'observed': commit,
             'changed': commit != source['commit']})
for repo in sorted({item['repo'] for item in lock['assets']}):
    releases = api('repos/' + repo + '/releases?per_page=10')
    release = next((item for item in releases if not item['draft']), None)
    pins = [item for item in lock['assets'] if item['repo'] == repo]
    observed = release['tag_name'] if release else None
    by_name = {item['name']: item for item in release['assets']} if release else {}
    mutated = observed == pins[0]['tag'] and any(
        by_name.get(item['name'], {}).get('digest') != 'sha256:' + item['sha256'] for item in pins)
    rows.append({'repo': repo, 'pinned': pins[0]['tag'], 'observed': observed,
                 'changed': observed != pins[0]['tag'] or mutated, 'asset_drift': mutated,
                 'prerelease': release['prerelease'] if release else None})
print(json.dumps({'channel': 'candidate', 'updates': rows}, indent=2))
