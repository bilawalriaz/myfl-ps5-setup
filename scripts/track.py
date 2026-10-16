#!/usr/bin/env python3
"""Report upstream drift; never update the reviewed lock or stable channel."""
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
lock = json.loads((root / 'deps.lock.json').read_text())
orbit = json.loads((root / 'orbit.lock.json').read_text())
store = json.loads((root / 'prosperostore.lock.json').read_text())
# The managed entry's transport is a deliberate source pin, not an installer update.
assets = [item for item in lock['assets'] if item['id'] != 'autoloader-transport-host']
assets += orbit['assets'] + [orbit['tv_app'], store['asset']]

def api(endpoint):
    return json.loads(subprocess.check_output(['gh', 'api', endpoint], text=True))

rows = []
source = lock['relapse']
commit = api('repos/' + source['repo'] + '/commits/main')['sha']
rows.append({'repo': source['repo'], 'pinned': source['commit'], 'observed': commit,
             'changed': commit != source['commit']})
for repo in sorted({item['repo'] for item in assets}):
    releases = api('repos/' + repo + '/releases?per_page=10')
    release = max((item for item in releases if not item['draft']),
                  key=lambda item: item['published_at'], default=None)
    pins = [item for item in assets if item['repo'] == repo]
    observed = release['tag_name'] if release else None
    by_name = {item['name']: item for item in release['assets']} if release else {}
    mutated = observed == pins[0]['tag'] and any(
        by_name.get(item['url'].rsplit('/', 1)[-1], {}).get('digest') != 'sha256:' + item['sha256'] for item in pins)
    rows.append({'repo': repo, 'pinned': pins[0]['tag'], 'observed': observed,
                 'changed': observed != pins[0]['tag'] or mutated, 'asset_drift': mutated,
                 'prerelease': release['prerelease'] if release else None})
print(json.dumps({'channel': 'candidate', 'updates': rows}, indent=2))
