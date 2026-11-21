"""Publish whitelisted generated files from a fresh disposable source snapshot.

Never rebase a generated artifact onto newer inputs. A rejected normal push
discards only this helper's temporary worktree and regenerates from origin/main.
The CLI is restricted to the existing GitHub Actions checkout.
"""
import fnmatch
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

PROFILES = {
    'images': (['apply_gmc_image_overrides.py', 'apply_screwdriver_voltage_confirmation.py', 'apply_screwdriver_bit_profiles.py', 'enrich_gmc_screwdriver_descriptions.py'], ['almighty-tools-gmc-*.xml'], 'Restore verified product images and screwdriver description details'),
    'compat': (['build_gmc_au_nz_compat.py'], ['almighty-tools-gmc-au-nz-au-compat.xml', 'almighty-tools-gmc-au-nz-nz-compat.xml'], 'Refresh AU NZ campaign compatibility feeds'),
    'christmas': (['test_gmc_us_christmas.py', 'build_gmc_us_christmas.py'], ['almighty-tools-gmc-us-dup.xml'], 'Refresh US Christmas gift feed from current US catalog'),
    'chatgpt': (['refresh_chatgpt_variant_options.py', 'refresh_chatgpt_qatar.py', 'refresh_chatgpt_german.py', 'build_chatgpt_feed.py', 'test_chatgpt_feed.py'], ['almighty-tools-chatgpt.csv', 'scripts/chatgpt-variant-options.json', 'scripts/chatgpt-qatar.xml', 'scripts/chatgpt-german-copy.json'], 'Refresh ChatGPT catalog for all Shopify markets'),
    'axon': (['test_axon_feed.py', 'build_axon_feed.py'], ['almighty-tools-axon-us.csv', 'scripts/axon-image-cache.json', 'scripts/axon-source-images.json', 'images/axon/*'], 'Refresh Axon US catalog from owned US feed'),
}


def git(repo, *args, check=True):
    return subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True, check=check, timeout=90)


def publish(repo, profile, *, temporary_root=None, attempts=5, sleep=time.sleep):
    commands, outputs, message = PROFILES[profile]
    repo = Path(repo).resolve()
    if git(repo, 'status', '--porcelain', '--untracked-files=no').stdout.strip():
        raise RuntimeError('Tracked checkout edits exist; refuse publication')
    for attempt in range(attempts):
        git(repo, 'fetch', 'origin', 'main')
        base = git(repo, 'rev-parse', 'FETCH_HEAD').stdout.strip()
        with tempfile.TemporaryDirectory(prefix='catalog-publish-', dir=temporary_root) as temp:
            snapshot = Path(temp) / 'snapshot'
            git(repo, 'worktree', 'add', '--detach', str(snapshot), base)
            try:
                env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
                for script in commands:
                    subprocess.run([sys.executable, 'scripts/' + script], cwd=snapshot, env=env, check=True, timeout=300)
                tracked = git(snapshot, 'diff', '--name-only', 'HEAD').stdout.splitlines()
                untracked = git(snapshot, 'ls-files', '--others', '--exclude-standard').stdout.splitlines()
                changed = tracked + [p for p in untracked if '__pycache__' not in Path(p).parts]
                if any(not any(fnmatch.fnmatchcase(p, rule) for rule in outputs) for p in changed):
                    raise RuntimeError('Generator changed a file outside its publication manifest')
                if not changed:
                    print('Generated outputs already current; no publication required', flush=True)
                    return {'status': 'unchanged', 'attempts': attempt + 1, 'source': base}
                git(snapshot, 'add', '--', *outputs)
                git(snapshot, '-c', 'user.name=github-actions[bot]', '-c', 'user.email=41898282+github-actions[bot]@users.noreply.github.com', 'commit', '-m', message)
                pushed = git(snapshot, 'push', 'origin', 'HEAD:main', check=False)
                if pushed.returncode == 0:
                    commit = git(snapshot, 'rev-parse', 'HEAD').stdout.strip()
                    print('Generated outputs published from current source ' + base, flush=True)
                    return {'status': 'published', 'attempts': attempt + 1, 'source': base, 'commit': commit}
                # Retry only the observed competing-ref failure. Authentication,
                # permission and policy errors must not be disguised as a race.
                error = pushed.stdout + pushed.stderr
                if not any(term in error for term in ['fetch first', 'non-fast-forward', 'cannot lock ref', 'stale info']):
                    raise RuntimeError('Git publication failed for a non-concurrency reason')
                print('Source advanced during generation; discard temporary result and regenerate', flush=True)
            finally:
                git(repo, 'worktree', 'remove', '--force', str(snapshot))
        if attempt + 1 < attempts:
            sleep(min(5 * (attempt + 1), 20))
    raise RuntimeError('Publication source kept changing; prior remote artifacts retained')


def main():
    repo = Path(__file__).resolve().parents[1]
    if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('GITHUB_REPOSITORY') != 'AlmightyTools/Meta-Catalog':
        raise SystemExit('Publication is allowed only in the existing repository GitHub Actions job')
    if Path(os.environ.get('GITHUB_WORKSPACE', '')).resolve() != repo:
        raise SystemExit('Unexpected Actions checkout')
    if len(sys.argv) != 2 or sys.argv[1] not in PROFILES:
        raise SystemExit('Pass an approved generated-feed profile')
    print(publish(repo, sys.argv[1], temporary_root=os.environ.get('RUNNER_TEMP')), flush=True)


if __name__ == '__main__':
    main()
