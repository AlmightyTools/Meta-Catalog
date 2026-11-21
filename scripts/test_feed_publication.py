import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import publish_generated_feed as publisher
from feed_public_json import read_json


def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True, stderr=subprocess.DEVNULL).strip()


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.remote = self.root / 'remote.git'
        subprocess.run(['git', 'init', '--bare', '--initial-branch=main', str(self.remote)], check=True, capture_output=True)
        self.repo = self.root / 'repo'
        subprocess.run(['git', 'clone', str(self.remote), str(self.repo)], check=True, capture_output=True)
        git(self.repo, 'config', 'user.name', 'Isolated test')
        git(self.repo, 'config', 'user.email', 'isolated@example.invalid')
        (self.repo / 'scripts').mkdir()
        (self.repo / 'source.txt').write_text('first')
        (self.repo / 'generated.txt').write_text('last-good')
        self.other = self.root / 'other'
        self.marker = self.root / 'race-once'

    def tearDown(self):
        self.temp.cleanup()

    def seed(self, generator):
        (self.repo / 'scripts/generate.py').write_text(generator)
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-m', 'fixture')
        git(self.repo, 'push', 'origin', 'main')
        self.initial = git(self.repo, 'rev-parse', 'HEAD')
        subprocess.run(['git', 'clone', str(self.remote), str(self.other)], check=True, capture_output=True)
        git(self.other, 'config', 'user.name', 'Competing source publisher')
        git(self.other, 'config', 'user.email', 'competitor@example.invalid')

    def run_profile(self):
        with patch.dict(publisher.PROFILES, {'fixture': (['generate.py'], ['generated.txt'], 'generated output')}):
            return publisher.publish(self.repo, 'fixture', temporary_root=self.root, sleep=lambda _: None)

    def test_rejected_push_regenerates_against_competing_source(self):
        self.seed("""from pathlib import Path
import subprocess
other=Path(%r)
marker=Path(%r)
if not marker.exists():
 (other/'source.txt').write_text('second')
 subprocess.run(['git','-C',str(other),'add','source.txt'],check=True)
 subprocess.run(['git','-C',str(other),'commit','-m','advance source'],check=True,capture_output=True)
 subprocess.run(['git','-C',str(other),'push','origin','main'],check=True,capture_output=True)
 marker.touch()
Path('generated.txt').write_text(Path('source.txt').read_text())
""" % (str(self.other), str(self.marker)))
        result = self.run_profile()
        self.assertEqual(result['attempts'], 2)
        self.assertEqual(git(self.remote, 'show', 'main:generated.txt'), 'second')
        self.assertEqual(git(self.remote, 'show', 'main:source.txt'), 'second')
        self.assertEqual(git(self.repo, 'rev-parse', 'HEAD'), self.initial)
        self.assertFalse(git(self.repo, 'status', '--porcelain'))
        self.assertEqual(git(self.remote, 'log', '--format=%s').splitlines().count('generated output'), 1)

    def test_failed_generation_preserves_last_published_artifact(self):
        self.seed("from pathlib import Path\nPath('generated.txt').write_text('invalid')\nraise SystemExit(2)\n")
        with self.assertRaises(subprocess.CalledProcessError):
            self.run_profile()
        self.assertEqual(git(self.remote, 'rev-parse', 'main'), self.initial)
        self.assertEqual(git(self.remote, 'show', 'main:generated.txt'), 'last-good')

    def test_generator_cannot_publish_source_or_unlisted_files(self):
        self.seed("from pathlib import Path\nPath('source.txt').write_text('unexpected edit')\nPath('generated.txt').write_text('bad')\n")
        with self.assertRaisesRegex(RuntimeError, 'manifest'):
            self.run_profile()
        self.assertEqual(git(self.remote, 'rev-parse', 'main'), self.initial)

    def test_local_cli_fails_before_any_remote_operation(self):
        env = dict(os.environ)
        env.pop('GITHUB_ACTIONS', None)
        result = subprocess.run([sys.executable, str(Path(publisher.__file__)), 'images'], env=env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('only', result.stderr)


class PublicReadTests(unittest.TestCase):
    def test_429_honors_retry_after_then_returns_real_response(self):
        calls, delays = [], []
        def opener(request, timeout):
            calls.append(request)
            if len(calls) == 1:
                raise HTTPError('https://public.example.invalid', 429, 'busy', {'Retry-After': '17'}, io.BytesIO(b''))
            return io.BytesIO(b'{"actual": 12.34}')
        self.assertEqual(read_json('same-public-request', opener=opener, sleep=delays.append), {'actual': 12.34})
        self.assertEqual(delays, [17])
        self.assertEqual(calls, ['same-public-request'] * 2)

    def test_forbidden_and_invalid_json_are_not_retried(self):
        for failure in [HTTPError('https://public.example.invalid', 403, 'forbidden', {}, io.BytesIO(b'')), json.JSONDecodeError('invalid', '', 0)]:
            calls = []
            def opener(request, timeout):
                calls.append(1)
                raise failure
            with self.assertRaises(type(failure)):
                read_json('same', opener=opener, sleep=lambda _: self.fail('No retry permitted'))
            self.assertEqual(len(calls), 1)

    def test_retry_bound_keeps_failure_visible(self):
        calls, delays = [], []
        def opener(request, timeout):
            calls.append(1)
            raise HTTPError('https://public.example.invalid', 503, 'busy', {}, io.BytesIO(b''))
        with self.assertRaises(HTTPError):
            read_json('same', opener=opener, sleep=delays.append)
        self.assertEqual(len(calls), 4)
        self.assertEqual(delays, [5, 10, 20])

    def test_long_provider_delay_is_not_cut_short(self):
        calls = []
        def opener(request, timeout):
            calls.append(1)
            raise HTTPError('https://public.example.invalid', 429, 'busy', {'Retry-After': '600'}, io.BytesIO(b''))
        with self.assertRaisesRegex(RuntimeError, 'Retry-After'):
            read_json('same', opener=opener, sleep=lambda _: self.fail('Must stop'))
        self.assertEqual(len(calls), 1)


if __name__ == '__main__':
    unittest.main()
