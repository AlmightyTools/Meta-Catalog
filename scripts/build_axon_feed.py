#!/usr/bin/env python3
"""Build Axon's public US catalog from the existing owned US Merchant feed."""
import csv
import hashlib
import html
import io
import json
import os
from pathlib import Path
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from decimal import Decimal

ROOT = Path(__file__).resolve().parents[1]
NS = {'g': 'http://base.google.com/ns/1.0'}
FIELDS = ['id', 'name', 'itemId', 'price', 'isAvailable', 'webUrl',
          'description', 'brand', 'categoryId', 'primaryImageUrl']
ASSET_BASE = 'https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/'
SHOPIFY_ORIGIN = 'https://checkout.almighty.tools'


def select_shopify_image(product, product_id, variant_id):
    """Use the variant's assigned photo, otherwise the product's first cover."""
    assert str(product['id']) == product_id, 'Shopify product identity changed'
    variants = [v for v in product['variants'] if str(v['id']) == variant_id]
    assert len(variants) == 1, 'Source variant missing from Shopify product'
    variant_image = variants[0].get('featured_image')
    if variant_image:
        assert str(variant_image.get('product_id', product_id)) == product_id
        url = variant_image['src']
        strategy = 'variant_featured_image'
    else:
        url = product.get('featured_image') or (product.get('images') or [None])[0]
        strategy = 'product_first_image'
    assert isinstance(url, str) and url, 'Shopify cover unavailable'
    if url.startswith('//'):
        url = 'https:' + url
    parsed = urllib.parse.urlsplit(url)
    assert parsed.scheme == 'https' and parsed.hostname == 'cdn.shopify.com', 'Unexpected Shopify cover host'
    return {'product_id': product_id, 'source_url': url, 'strategy': strategy}


def shopify_images(xml_bytes, previous=None):
    products = {}
    for item in ET.fromstring(xml_bytes).findall('.//item'):
        match = re.fullmatch(r'shopify_US_(\d+)_(\d+)', item.findtext('g:id', namespaces=NS))
        assert match, 'Unexpected source identity'
        product_id, variant_id = match.groups()
        path = urllib.parse.urlsplit(item.findtext('link')).path
        assert re.fullmatch(r'/products/(?:[a-z0-9-]|%[0-9A-Fa-f]{2})+', path), 'Unexpected product path'
        grouped = products.setdefault(product_id, {'path': path, 'variants': []})
        assert grouped['path'] == path, 'Conflicting product handles'
        grouped['variants'].append(variant_id)

    def fetch(entry):
        product_id, source = entry
        request = urllib.request.Request(SHOPIFY_ORIGIN + source['path'] + '.js',
                                         headers={'User-Agent': 'AlmightyTools-AxonFeed/1.0'})
        with urllib.request.urlopen(request, timeout=45) as response:
            assert urllib.parse.urlsplit(response.geturl()).hostname == 'checkout.almighty.tools', 'Unexpected product redirect'
            payload = response.read(5_000_001)
        assert len(payload) <= 5_000_000, 'Product response too large'
        product = json.loads(payload)
        return {v: select_shopify_image(product, product_id, v) for v in source['variants']}

    selected = {}
    previous = previous or {}
    rate_limited = False
    cached_products = 0
    for entry in products.items():
        product_id, source = entry
        mapping = None
        if not rate_limited:
            for attempt in range(2):
                try:
                    mapping = fetch(entry)
                    break
                except urllib.error.HTTPError as error:
                    if error.code != 429:
                        raise
                    if attempt == 0:
                        try: retry_after = float(error.headers.get('Retry-After', 2))
                        except (TypeError, ValueError): retry_after = 2
                        time.sleep(min(max(retry_after, 2), 60))
                    else:
                        rate_limited = True
            if mapping:
                time.sleep(.5)
        if mapping is None:
            # Respect Shopify's rate limit. Keep only our last verified ORIGINAL
            # mappings; never substitute Google images or guess a new variant.
            mapping = {}
            for variant_id in source['variants']:
                cached = previous.get(variant_id)
                assert cached and cached['product_id'] == product_id, 'No verified original image for rate-limited variant'
                assert cached['strategy'] in {'product_first_image', 'variant_featured_image'}
                mapping[variant_id] = cached
            cached_products += 1
        selected.update(mapping)
    if cached_products:
        print(json.dumps({'warning': 'SHOPIFY_IMAGE_REFRESH_RATE_LIMITED',
                          'verified_original_product_mappings_retained': cached_products,
                          'next_refresh_attempt': 'next scheduled build'}))
    return selected


def clean(value, limit):
    value = re.sub(r'<[^>]*>', ' ', html.unescape(value or ''))
    value = re.sub(r'\s+', ' ', value.replace(',', ';')).strip()
    return value[:limit]


def money(value):
    amount, currency = value.split()
    assert currency == 'USD', f'Unexpected currency: {currency}'
    number = Decimal(amount)
    assert number.is_finite() and number > 0, 'Invalid price'
    return number


def image_asset(url, cache, root):
    parsed = urllib.parse.urlsplit(url)
    assert parsed.scheme == 'https' and parsed.hostname in {
        'cdn.shopify.com', 'raw.githubusercontent.com'}, 'Unexpected image host'
    assert ',' not in url and '\n' not in url, 'Unsafe image URL'
    cached = cache.get(url)
    if cached and (root / cached).is_file():
        return ASSET_BASE + cached
    request = urllib.request.Request(url, headers={'User-Agent': 'AlmightyTools-AxonFeed/1.0'})
    with urllib.request.urlopen(request, timeout=45) as response:
        data = response.read(20_000_001)
    assert 0 < len(data) <= 20_000_000, 'Invalid image size'
    # Preserve original JPEG/PNG bytes (including any provenance metadata).
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        extension = 'png'
    elif data.startswith(b'\xff\xd8\xff'):
        extension = 'jpg'
    else:
        from PIL import Image
        with Image.open(io.BytesIO(data)) as image:
            assert image.width * image.height <= 80_000_000
            out = io.BytesIO()
            image.convert('RGB').save(out, format='JPEG', quality=95)
            data = out.getvalue()
        extension = 'jpg'
    digest = hashlib.sha256(data).hexdigest()
    path = f'images/axon/{digest}.{extension}'
    destination = root / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    cache[url] = path
    return ASSET_BASE + path


def build_items(xml_bytes, resolve_image, source_images=None):
    source = ET.fromstring(xml_bytes)
    rows = []
    seen = set()
    for item in source.findall('.//item'):
        def g(name):
            return item.findtext('g:' + name, default='', namespaces=NS)
        match = re.fullmatch(r'shopify_US_(\d+)_(\d+)', g('id'))
        assert match, 'Unexpected source identity'
        product_id, variant_id = match.groups()
        assert g('item_group_id') == product_id
        assert variant_id not in seen, 'Duplicate variant ID'
        seen.add(variant_id)
        url = item.findtext('link', default='')
        parts = urllib.parse.urlsplit(url)
        params = urllib.parse.parse_qs(parts.query)
        assert parts.scheme == 'https' and parts.hostname == 'almighty.tools'
        assert parts.path.startswith('/products/')
        assert params.get('variant') == [variant_id]
        assert params.get('country') == ['US']
        assert not params.get('currency') or params['currency'] == ['USD']
        regular = money(g('price'))
        current = money(g('sale_price')) if g('sale_price') else regular
        assert current <= regular, 'Sale exceeds base price'
        # Axon requires validity dates for salePrice; never invent promotion dates.
        # Export the actual payable price directly, with no artificial sale window.
        available = g('availability')
        assert available in {'in stock', 'out of stock', 'preorder', 'backorder'}
        category = g('google_product_category')
        assert not category or category.isdigit()
        if source_images is not None:
            assert source_images[variant_id]['product_id'] == product_id
            primary_image = source_images[variant_id]['source_url']
        else:
            primary_image = g('image_link')
        rows.append({
            'id': variant_id, 'name': clean(item.findtext('title'), 1024),
            'itemId': product_id, 'price': f'{current:.2f}',
            'isAvailable': 'TRUE' if available == 'in stock' else 'FALSE',
            'webUrl': url, 'description': clean(item.findtext('description'), 8192),
            'brand': 'The Almighty Tools®', 'categoryId': category,
            'primaryImageUrl': resolve_image(primary_image),
        })
    assert len(rows) >= 80, 'Source unexpectedly small; keep prior feed'
    for row in rows:
        assert all(row[k] for k in ['id', 'name', 'itemId', 'price', 'webUrl', 'primaryImageUrl'])
        assert all(not any(c in v for c in ',\r\n') for v in row.values())
        assert urllib.parse.urlsplit(row['primaryImageUrl']).path.endswith(('.jpg', '.jpeg', '.png'))
    return rows


def atomic_write(path, value):
    with tempfile.NamedTemporaryFile('w', dir=path.parent, delete=False, encoding='utf-8', newline='') as output:
        output.write(value)
        temporary = output.name
    os.replace(temporary, path)


def main():
    source_path = ROOT / 'almighty-tools-gmc-us.xml'
    output_path = ROOT / 'almighty-tools-axon-us.csv'
    cache_path = ROOT / 'scripts/axon-image-cache.json'
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    xml_bytes = source_path.read_bytes()
    source_map_path = ROOT / 'scripts/axon-source-images.json'
    previous_images = json.loads(source_map_path.read_text()) if source_map_path.exists() else {}
    source_images = shopify_images(xml_bytes, previous_images)
    rows = build_items(xml_bytes, lambda url: image_asset(url, cache, ROOT), source_images)
    if output_path.exists():
        previous = list(csv.DictReader(output_path.open(encoding='utf-8')))
        assert len(rows) >= len(previous) * .8, 'Source shrank by over 20%; review before replacing'
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    # Only replace the public feed after the whole source and all images pass.
    atomic_write(cache_path, json.dumps(cache, indent=2, sort_keys=True) + '\n')
    atomic_write(source_map_path, json.dumps(source_images, indent=2, sort_keys=True) + '\n')
    atomic_write(output_path, output.getvalue())
    print(json.dumps({'status': 'AXON_FEED_READY', 'variants': len(rows),
                      'products': len({r['itemId'] for r in rows}),
                      'available': sum(r['isAvailable'] == 'TRUE' for r in rows),
                      'image_assets': len(set(cache.values())),
                      'source_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
