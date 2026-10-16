"""The tracker must report publication order and every downloadable app."""
import contextlib
import io
import json
from pathlib import Path
import runpy
import shutil
import tempfile
import unittest
from unittest.mock import patch


class TrackerTests(unittest.TestCase):
    def test_publication_order_store_coverage_and_fixed_transport(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'scripts').mkdir()
            script = root / 'scripts' / 'track.py'
            shutil.copyfile(Path(__file__).with_name('track.py'), script)
            def asset(repo, tag, identifier):
                return dict(repo=repo, tag=tag, id=identifier,
                            url='https://github.com/' + repo + '/payload.elf', sha256='a' * 64)
            lock = dict(relapse=dict(repo='owner/relapse', commit='current'), assets=[
                asset('owner/autoloader', 'v2', 'autoloader-installer'),
                asset('owner/autoloader', 'v1', 'autoloader-transport-host')])
            orbit = dict(assets=[asset('owner/orbit', 'v2', 'orbit')],
                         tv_app=asset('owner/orbit', 'v2', 'orbit-tv'))
            store = dict(asset=asset('owner/store', 'v1', 'prosperostore-app'))
            for name, value in [('deps', lock), ('orbit', orbit), ('prosperostore', store)]:
                (root / (name + '.lock.json')).write_text(json.dumps(value))
            def api(args, **kwargs):
                if args[-1].endswith('/commits/main'):
                    return json.dumps({'sha': 'current'})
                # GitHub's array order can differ from publication order.
                return json.dumps([dict(tag_name=tag, published_at=date, draft=False,
                    prerelease=False, assets=[dict(name='payload.elf', digest='sha256:' + 'a' * 64)])
                    for tag, date in [('v1', '2026-10-10T12:00:00Z'),
                                      ('v2', '2026-10-10T18:00:00Z')]])
            output = io.StringIO()
            with patch('subprocess.check_output', side_effect=api), contextlib.redirect_stdout(output):
                runpy.run_path(str(script), run_name='__main__')
            rows = {row['repo']: row for row in json.loads(output.getvalue())['updates']}
            self.assertEqual(rows['owner/autoloader']['observed'], 'v2')
            self.assertFalse(rows['owner/autoloader']['changed'])
            self.assertFalse(rows['owner/orbit']['changed'])
            self.assertTrue(rows['owner/store']['changed'])


if __name__ == '__main__':
    unittest.main()
