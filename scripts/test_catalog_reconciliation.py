import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

import catalog_http
import reconcile_catalog_feeds as reconcile


class CatalogHTTPTests(unittest.TestCase):
    def test_rate_limit_and_timeout_backoff(self):
        rate_limit = HTTPError('https://checkout.almighty.tools', 429, 'rate limit',
                               {'Retry-After': '10'}, None)
        with patch.object(catalog_http, 'urlopen',
                          side_effect=[rate_limit, TimeoutError(), io.BytesIO(b'{"id": 1}')]), \
             patch.object(catalog_http.time, 'sleep') as sleep:
            self.assertEqual(catalog_http.read_json('request', timeout=30), {'id': 1})
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [10, 4])

    def test_long_retry_after_is_not_ignored(self):
        rate_limit = HTTPError('https://checkout.almighty.tools', 429, 'rate limit',
                               {'Retry-After': '90'}, None)
        with patch.object(catalog_http, 'urlopen', side_effect=rate_limit) as request, \
             patch.object(catalog_http.time, 'sleep') as sleep:
            with self.assertRaises(HTTPError):
                catalog_http.read_json('request', timeout=30)
        request.assert_called_once()
        sleep.assert_not_called()


class CatalogPublicationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.origin = root / 'origin.git'
        self.publisher = root / 'publisher'
        self.upstream = root / 'upstream'
        self.git(root, 'init', '--bare', '--initial-branch=main', str(self.origin))
        self.git(root, 'clone', str(self.origin), str(self.publisher))
        self.configure(self.publisher)
        (self.publisher / 'scripts').mkdir()
        (self.publisher / reconcile.US).write_text('input\n')
        (self.publisher / 'almighty-tools-chatgpt.csv').write_text('previous\n')
        self.git(self.publisher, 'add', '.')
        self.git(self.publisher, 'commit', '-m', 'initial')
        self.git(self.publisher, 'push', 'origin', 'main')
        self.git(root, 'clone', str(self.origin), str(self.upstream))
        self.configure(self.upstream)

    @staticmethod
    def git(directory, *args):
        return subprocess.run(['git', *args], cwd=directory, check=True, text=True,
                              capture_output=True).stdout

    def configure(self, directory):
        self.git(directory, 'config', 'user.name', 'Test')
        self.git(directory, 'config', 'user.email', 'test@example.invalid')

    def advance(self, path):
        (self.upstream / path).write_text('upstream update\n')
        self.git(self.upstream, 'add', path)
        self.git(self.upstream, 'commit', '-m', 'upstream')
        self.git(self.upstream, 'push', 'origin', 'main')

    def stage_candidate(self):
        output = 'almighty-tools-chatgpt.csv'
        (self.publisher / output).write_text('candidate\n')
        self.git(self.publisher, 'add', output)

    def read_remote(self, path):
        return self.git(self.origin, 'show', f'main:{path}')

    def test_never_publishes_against_new_regional_input(self):
        self.stage_candidate()
        self.advance(reconcile.US)
        with patch.object(reconcile, 'ROOT', self.publisher):
            self.assertFalse(reconcile.publish())
        self.assertEqual(self.read_remote('almighty-tools-chatgpt.csv'), 'previous\n')
        self.assertEqual(self.read_remote(reconcile.US), 'upstream update\n')

    def test_reuses_candidate_when_unrelated_feed_advances(self):
        self.stage_candidate()
        self.advance('meta-catalog-feed.xml')
        with patch.object(reconcile, 'ROOT', self.publisher):
            self.assertTrue(reconcile.publish())
        self.assertEqual(self.read_remote('almighty-tools-chatgpt.csv'), 'candidate\n')
        self.assertEqual(self.read_remote('meta-catalog-feed.xml'), 'upstream update\n')

    def test_keeps_last_outputs_and_skips_work_during_batch(self):
        with patch.object(reconcile, 'ROOT', self.publisher), \
             patch.object(reconcile, 'build_gmc') as build:
            self.assertEqual(reconcile.main(), 0)
        build.assert_not_called()
        self.assertEqual(self.read_remote('almighty-tools-chatgpt.csv'), 'previous\n')

    def test_failed_stage_keeps_prior_output_and_allows_successful_stage(self):
        def refresh_gmc():
            (self.publisher / reconcile.US).write_text('corrected\n')

        def fail_chatgpt():
            (self.publisher / 'almighty-tools-chatgpt.csv').write_text('incomplete\n')
            raise subprocess.CalledProcessError(1, 'build')

        with patch.object(reconcile, 'ROOT', self.publisher), \
             patch.object(reconcile.time, 'time', return_value=2_000_000_000), \
             patch.object(reconcile, 'CHATGPT_OUTPUTS', ('almighty-tools-chatgpt.csv',)), \
             patch.object(reconcile, 'AXON_OUTPUTS', (reconcile.US,)), \
             patch.object(reconcile, 'build_gmc', side_effect=refresh_gmc), \
             patch.object(reconcile, 'build_chatgpt', side_effect=fail_chatgpt), \
             patch.object(reconcile, 'build_axon'):
            self.assertEqual(reconcile.main(), 1)
        self.assertEqual(self.read_remote(reconcile.US), 'corrected\n')
        self.assertEqual(self.read_remote('almighty-tools-chatgpt.csv'), 'previous\n')


if __name__ == '__main__':
    unittest.main()
