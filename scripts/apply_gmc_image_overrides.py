"""Apply narrowly scoped image-only corrections after source feed refreshes."""
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
G = '{http://base.google.com/ns/1.0}'
POLICY = json.loads((ROOT / 'scripts/gmc-image-overrides.json').read_text())['variants']
IMAGE_ROOT = 'https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/images/google-merchant/'


def strip_images(text):
    return re.sub(r'<g:(?:image_link|additional_image_link)>.*?</g:(?:image_link|additional_image_link)>', '', text, flags=re.S)


def normalize(raw):
    source = raw.decode('utf-8')
    count = 0
    def convert(match):
        nonlocal count
        original = match.group(0)
        item = ET.fromstring(original.replace('<item>', '<item xmlns:g="http://base.google.com/ns/1.0">', 1))
        identity = item.findtext(G + 'id') or ''
        ids = re.fullmatch(r'(?:Shopify_|shopify_(?:AU|NZ)_|dup_US_)(\d+)_(\d+)', identity)
        if not ids or ids[2] not in POLICY:
            return original
        rule = POLICY[ids[2]]
        if ids[1] != rule['product_id']:
            raise ValueError('Variant/product mismatch: ' + identity)
        image = IMAGE_ROOT + rule['filename']
        result, replacements = re.subn(r'<g:image_link>.*?</g:image_link>', '<g:image_link>' + image + '</g:image_link>', original, flags=re.S)
        if replacements != 1:
            raise ValueError('Expected one main image: ' + identity)
        if rule['remove_additional_images']:
            result = re.sub(r'<g:additional_image_link>.*?</g:additional_image_link>', '', result, flags=re.S)
        if strip_images(result) != strip_images(original):
            raise ValueError('Non-image content changed')
        count += 1
        return result
    output = re.sub(r'<item>.*?</item>', convert, source, flags=re.S)
    ET.fromstring(output)
    if strip_images(output) != strip_images(source):
        raise ValueError('Feed content other than images changed')
    return output.encode('utf-8'), count


def main():
    candidates = {}
    total = 0
    for path in sorted(ROOT.glob('almighty-tools-gmc-*.xml')):
        raw = path.read_bytes()
        output, count = normalize(raw)
        total += count
        if output != raw:
            candidates[path] = output
    # Validate all feeds before replacing any; retain unrelated feed bytes.
    for path, output in candidates.items():
        temporary = path.with_suffix('.xml.tmp')
        temporary.write_bytes(output)
        temporary.replace(path)
    print(f'GMC image policy: {total} mapped offers; {len(candidates)} feeds updated')


if __name__ == '__main__':
    main()
