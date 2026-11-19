#!/usr/bin/env python3
"""Build the independent Christmas assortment from the current canonical US XML."""
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
G = '{http://base.google.com/ns/1.0}'
SOURCE = ROOT / 'almighty-tools-gmc-us.xml'
OUTPUT = ROOT / 'almighty-tools-gmc-us-dup.xml'


def gift_description(item):
    category = (item.findtext(G + 'product_type') or '').lower()
    if 'gift card' in category or 'gift card' in (item.findtext(G + 'structured_title/' + G + 'content') or '').lower():
        return 'A Christmas gift option that lets the recipient choose their own items.'
    if any(word in category for word in ('camping', 'outdoor', 'carabiner')):
        return 'A Christmas gift idea for someone who enjoys outdoor activities.'
    if any(word in category for word in ('smartwatch', 'phone', 'power bank', 'radio')):
        return 'A practical Christmas gift idea for everyday use.'
    if any(word in category for word in ('cushion', 'pillow', 'backpack', 'boots', 'mask', 'vacuum', 'cleaner')):
        return 'A practical Christmas gift idea for home or everyday use.'
    return 'A practical Christmas gift idea for DIY enthusiasts and home projects.'


def build(raw):
    text = raw.decode('utf-8')
    items = ET.fromstring(raw).findall('./channel/item')
    if len(items) < 100:
        raise ValueError('Canonical US assortment unexpectedly has fewer than 100 offers')
    seen = set()
    def convert(match):
        original = match.group(0)
        item = ET.fromstring(original.replace('<item>', '<item xmlns:g="http://base.google.com/ns/1.0">', 1))
        identity = item.findtext(G + 'id') or ''
        ids = re.fullmatch(r'Shopify_(\d+)_(\d+)', identity)
        if not ids or identity in seen:
            raise ValueError('Invalid or duplicate canonical identity')
        seen.add(identity)
        product, variant = ids.groups()
        if item.findtext(G + 'item_group_id') != product:
            raise ValueError('Product group does not match identity')
        link = urlsplit(item.findtext('link') or '')
        query = parse_qs(link.query)
        if link.hostname != 'almighty.tools' or query.get('country') != ['US'] or query.get('variant') != [variant]:
            raise ValueError('Unexpected US landing page')
        if not (item.findtext(G + 'price') or '').endswith(' USD'):
            raise ValueError('Unexpected currency')
        if any(item.find(G + name) is not None for name in ('title', 'description', 'custom_label_3', 'custom_label_4')):
            raise ValueError('Ambiguous copy or occupied campaign labels')
        result = original.replace('<g:id>' + identity + '</g:id>', '<g:id>dup_US_' + product + '_' + variant + '</g:id>', 1)
        result = result.replace('<g:item_group_id>' + product + '</g:item_group_id>', '<g:item_group_id>dup_US_' + product + '</g:item_group_id>', 1)
        if len('dup_US_' + product + '_' + variant) > 50:
            raise ValueError('Duplicate ID exceeds 50 characters')
        for field, limit in (('structured_title', 150), ('structured_description', 5000)):
            element = item.find(G + field)
            if element is None or element.findtext(G + 'digital_source_type') != 'trained_algorithmic_media':
                raise ValueError('Expected marked structured source copy')
            content = element.findtext(G + 'content') or ''
            if not content.strip():
                raise ValueError('Empty source copy')
            new = 'Christmas Gift - ' + content if field == 'structured_title' else gift_description(item) + ' ' + content
            if len(new) > limit:
                raise ValueError('Christmas copy exceeds Google field limit; preserve variant details')
            pattern = r'(<g:' + field + r'>.*?<g:content>).*?(</g:content>.*?</g:' + field + r'>)'
            result, count = re.subn(pattern, lambda m: m[1] + escape(new) + m[2], result, flags=re.S)
            if count != 1:
                raise ValueError('Ambiguous structured field')
        return result.replace('</item>', '<g:custom_label_3>christmas_gifts</g:custom_label_3><g:custom_label_4>dup</g:custom_label_4></item>')
    output, count = re.subn(r'<item>.*?</item>', convert, text, flags=re.S)
    if count != len(items):
        raise ValueError('Unexpected item serialization')
    ET.fromstring(output)
    return output.encode('utf-8')


if __name__ == '__main__':
    output = build(SOURCE.read_bytes())
    temporary = OUTPUT.with_suffix('.xml.tmp')
    temporary.write_bytes(output)
    temporary.replace(OUTPUT)
    print('Christmas US feed: %d offers, source attributes preserved' % len(ET.fromstring(output).findall('./channel/item')))
