"""Preserve AU_NZ_OWNED campaign identities while consuming current market data."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit, parse_qs

ROOT = Path(__file__).resolve().parents[1]
NS = {'g': 'http://base.google.com/ns/1.0'}


def convert(raw, country):
    assert country in {'AU', 'NZ'}
    text = raw.decode('utf-8')
    items = ET.fromstring(raw).findall('./channel/item')
    assert len(items) >= 100, 'Incomplete source; retain preceding compatibility feeds'
    ids = set()
    for item in items:
        ident = item.findtext('g:id', namespaces=NS)
        match = re.fullmatch(r'Shopify_(\d+)_(\d+)', ident)
        assert match, 'Unexpected primary GMC identity'
        pid, vid = match.groups()
        assert pid == item.findtext('g:item_group_id', namespaces=NS)
        assert vid not in ids, 'Duplicate variant'
        ids.add(vid)
        url = urlsplit(item.findtext('link'))
        params = parse_qs(url.query)
        assert url.scheme == 'https' and url.hostname == 'almighty.tools'
        assert params.get('country') == [country] and params.get('variant') == [vid]
        for field in ['price', 'sale_price']:
            value = item.findtext('g:' + field, namespaces=NS)
            if value:
                assert value.split()[-1] == 'USD', 'AU/NZ compatibility is USD only'
    updated, count = re.subn(r'<g:id>Shopify_(\d+)_(\d+)</g:id>',
                             lambda m: f'<g:id>shopify_{country}_{m[1]}_{m[2]}</g:id>', text)
    assert count == len(items)
    assert re.sub(r'<g:id>[^<]+</g:id>', '', text) == re.sub(r'<g:id>[^<]+</g:id>', '', updated)
    return updated.encode('utf-8')


def main():
    candidates = {}
    for country in ['AU', 'NZ']:
        source = ROOT / f'almighty-tools-gmc-{country.lower()}.xml'
        target = ROOT / f'almighty-tools-gmc-au-nz-{country.lower()}-compat.xml'
        candidates[target] = convert(source.read_bytes(), country)
    # Validate both sources before replacing either output.
    for target, data in candidates.items():
        temporary = target.with_suffix('.tmp')
        temporary.write_bytes(data)
        temporary.replace(target)
        print('GMC_AU_NZ_COMPAT_READY', target.name)


if __name__ == '__main__':
    main()
