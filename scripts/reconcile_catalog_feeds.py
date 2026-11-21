"""Refresh derived feeds from one settled checkout and publish verified changes."""

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = 'scripts/catalog-feed-state.json'
QUIET_SECONDS = 6 * 60
GMC = 'almighty-tools-gmc-*.xml'
US = 'almighty-tools-gmc-us.xml'
GMC_SCRIPTS = (
    'apply_gmc_image_overrides', 'apply_screwdriver_voltage_confirmation',
    'apply_screwdriver_bit_profiles', 'enrich_gmc_screwdriver_descriptions',
)
GMC_INPUTS = (
    GMC, 'scripts/gmc-image-overrides.json',
    *(f'scripts/{name}.py' for name in GMC_SCRIPTS),
    'scripts/*gmc_au_nz_compat.py', 'scripts/*gmc_us_christmas.py',
)
CHATGPT_OUTPUTS = (
    'almighty-tools-chatgpt.csv', 'scripts/chatgpt-variant-options.json',
    'scripts/chatgpt-qatar.xml', 'scripts/chatgpt-german-copy.json',
)
CHATGPT_INPUTS = (
    GMC, 'scripts/*chatgpt*.py', 'scripts/chatgpt-markets.json',
    'scripts/chatgpt-locales.json', 'scripts/catalog_http.py', *CHATGPT_OUTPUTS,
)
AXON_OUTPUTS = (
    'almighty-tools-axon-us.csv', 'scripts/axon-image-cache.json',
    'scripts/axon-source-images.json', 'images/axon/',
)
AXON_INPUTS = (US, 'scripts/*axon*.py', 'scripts/axon-product-copy.json', *AXON_OUTPUTS)
CONFIG = ('scripts/reconcile_catalog_feeds.py', '.github/workflows/catalog-feeds.yml')
WATCHED = (*GMC_INPUTS, *CHATGPT_INPUTS, *AXON_INPUTS, *CONFIG, STATE)


def git(*args, check=True):
    return subprocess.run(['git', *args], cwd=ROOT, check=check,
                          text=True, stdout=subprocess.PIPE)


def run(*names):
    for name in names:
        subprocess.run([sys.executable, f'scripts/{name}.py'], cwd=ROOT, check=True)


def fingerprint(paths):
    digest = hashlib.sha256()
    for path in sorted({p for pattern in paths for p in ROOT.glob(pattern)}):
        files = sorted(p for p in path.rglob('*') if p.is_file()) if path.is_dir() else [path]
        for file in files:
            digest.update(str(file.relative_to(ROOT)).encode() + b'\0')
            digest.update(hashlib.sha256(file.read_bytes()).digest())
    return digest.hexdigest()


def due(record, inputs, interval, now):
    return record.get('inputs') != fingerprint(inputs) or (
        interval is not None and now - record.get('refreshed', 0) >= interval
    )


def build_gmc():
    # Apply corrections before deriving feeds and then reconcile the derived XML.
    run(*GMC_SCRIPTS)
    run('test_gmc_image_overrides', 'test_gmc_us_christmas',
        'build_gmc_au_nz_compat', 'build_gmc_us_christmas')
    run(*GMC_SCRIPTS)


def build_chatgpt():
    run('refresh_chatgpt_variant_options', 'refresh_chatgpt_qatar',
        'refresh_chatgpt_german', 'build_chatgpt_feed', 'test_chatgpt_feed')


def build_axon():
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'Pillow==13.0.0'],
                   cwd=ROOT, check=True)
    run('test_axon_feed', 'build_axon_feed')


def publish():
    if git('diff', '--cached', '--quiet', check=False).returncode == 0:
        return True
    git('commit', '-m', 'Reconcile derived catalog feeds')
    for attempt in range(4):
        git('fetch', 'origin', 'main')
        if git('diff', '--name-only', 'HEAD^', 'origin/main', '--', *WATCHED).stdout:
            print('Catalog inputs or outputs advanced; defer to the next settled checkout.', flush=True)
            return False
        if git('rebase', 'origin/main', check=False).returncode:
            git('rebase', '--abort')
            print('Concurrent change could not be safely rebased; deferring publication.', flush=True)
            return False
        if git('push', 'origin', 'HEAD:main', check=False).returncode == 0:
            return True
        time.sleep(2 ** attempt)
    raise RuntimeError('Unable to publish after four Git attempts')


def main():
    if git('status', '--porcelain').stdout:
        raise RuntimeError('Catalog reconciliation requires a clean checkout')
    now = int(time.time())
    # Ignore hourly commits for Meta, Microsoft, and reviews when checking for a quiet batch.
    latest = git('log', '-1', '--format=%ct', '--', *GMC_INPUTS).stdout.strip()
    if latest and now - int(latest) < QUIET_SECONDS:
        print('Regional feeds are still settling; the next scheduled run will recheck.')
        return 0
    state_path = ROOT / STATE
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    stages = (
        ('gmc', GMC_INPUTS, (GMC,), None, build_gmc),
        ('chatgpt', CHATGPT_INPUTS, CHATGPT_OUTPUTS, 6 * 3600, build_chatgpt),
        ('axon', AXON_INPUTS, AXON_OUTPUTS, 24 * 3600, build_axon),
    )
    failures = []
    for name, inputs, outputs, interval, build in stages:
        if not due(state.get(name, {}), inputs, interval, now):
            continue
        try:
            build()
        except subprocess.CalledProcessError:
            # The index preserves completed stages. Restore this stage's last good files.
            git('restore', '--worktree', '--', *outputs)
            git('clean', '-fd', '--', *outputs)
            if name == 'gmc':
                raise
            failures.append(name)
            continue
        git('add', '--', *outputs)
        state[name] = {'inputs': fingerprint(inputs), 'refreshed': now}
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + '\n')
    git('add', '--', STATE)
    git('config', 'user.name', 'github-actions[bot]')
    git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    published = publish()
    if failures:
        print('Preserved previously published outputs for failed stages: ' + ', '.join(failures))
    elif published:
        print('Catalog reconciliation finished.')
    return bool(failures)


if __name__ == '__main__':
    sys.exit(main())
