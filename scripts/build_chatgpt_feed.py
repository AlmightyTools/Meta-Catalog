"""Build OpenAI discovery CSV from canonical country catalogs without changing them."""
import collections
import csv
import io
import json
import re
import xml.etree.ElementTree as ET
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qs, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
G = '{http://base.google.com/ns/1.0}'
FIELDS = ['item_id','title','description','url','brand','seller_name','image_url',
          'availability','price','sale_price','group_id','listing_has_variations',
          'variant_dict','gtin','condition','product_category','additional_image_urls',
          'target_countries','store_country','is_eligible_search','is_ads_eligible']
REQUIRED = FIELDS[:9] + ['target_countries','store_country']
AVAILABILITY = {'in stock':'in_stock','out of stock':'out_of_stock',
                'preorder':'pre_order','pre order':'pre_order','backorder':'backorder',
                'unknown':'unknown'}


def localized_source(country, locale):
    source = ROOT/('scripts/chatgpt-qatar.xml' if country == 'QA' else 'almighty-tools-gmc-'+country.lower()+'.xml')
    if locale in {'es','fr'}:
        source = ROOT/('almighty-tools-gmc-'+country.lower()+'-'+locale+'.xml')
    raw = source.read_bytes()
    if locale == 'de':
        tree = ET.fromstring(raw)
        copy = json.loads((ROOT/'scripts/chatgpt-german-copy.json').read_text())
        for item in tree.findall('./channel/item'):
            link = item.find('link')
            parsed = urlsplit(link.text)
            text = copy[parsed.path]
            link.text = urlunsplit(parsed._replace(path='/de'+parsed.path))
            for name in ['title','description']:
                field = item.find(G+'structured_'+name+'/'+G+'content')
                if field is None: field = item.find(G+name)
                if field is None: field = ET.SubElement(item,G+name)
                field.text = text[name]
        raw = ET.tostring(tree,encoding='utf-8')
    return raw


def valid_gtin(value):
    if not re.fullmatch(r'(?:\d{8}|\d{12}|\d{13}|\d{14})', value):
        return False
    digits = [int(d) for d in value]
    return (sum(d * (3 if i % 2 == 0 else 1) for i,d in enumerate(reversed(digits[:-1]))) + digits[-1]) % 10 == 0


def money(value, currency):
    if not re.fullmatch(r'\d+(?:\.\d+)? ' + currency, value):
        raise ValueError('Wrong market currency: ' + value)
    amount = Decimal(value.split()[0])
    if amount <= 0:
        raise ValueError('Nonpositive item price')
    return amount


def build(raw, options, country='US', currency='USD'):
    items = ET.fromstring(raw).findall('./channel/item')
    if len(items) < 100:
        raise ValueError('Incomplete canonical catalog; retain previous CSV')
    counts = collections.Counter(i.findtext(G+'item_group_id') for i in items)
    rows, seen, combinations, omitted_gtins = [], set(), collections.defaultdict(set), []
    for item in items:
        def field(name): return item.findtext(G+name) or ''
        ident = field('id')
        ids = re.fullmatch(r'Shopify_(\d+)_(\d+)',ident)
        if not ids or ident in seen:
            raise ValueError('Invalid or duplicate canonical identity')
        seen.add(ident)
        pid, vid = ids.groups()
        if field('item_group_id') != pid:
            raise ValueError('Identity/group mismatch')
        url = item.findtext('link') or ''
        parsed = urlsplit(url)
        query = parse_qs(parsed.query)
        if parsed.scheme != 'https' or parsed.hostname != 'almighty.tools' or query.get('variant') != [vid] or query.get('country') != [country]:
            raise ValueError('Wrong product/variant/market URL')
        title = item.findtext(G+'structured_title/'+G+'content') or field('title')
        description = item.findtext(G+'structured_description/'+G+'content') or field('description')
        if not 0 < len(title) <= 150 or not 0 < len(description) <= 5000:
            raise ValueError('Missing or excessive product copy')
        image = field('image_link')
        if urlsplit(image).scheme != 'https' or not urlsplit(image).hostname:
            raise ValueError('Invalid main image URL')
        regular = money(field('price'), currency)
        sale = field('sale_price')
        if sale and money(sale, currency) >= regular:
            raise ValueError('Invalid sale price')
        availability = AVAILABILITY.get(field('availability'))
        if not availability:
            raise ValueError('Unrecognized source availability')
        row = dict(item_id='Shopify_'+country+'_'+pid+'_'+vid, title=title, description=description, url=url,
                   brand=field('brand'), seller_name='The Almighty Tools®', image_url=image,
                   availability=availability, price=field('price'), sale_price=sale,
                   group_id=country+'_'+pid, condition=field('condition'), product_category=field('product_type'),
                   target_countries=json.dumps([country]), store_country='US',
                   is_eligible_search='true', is_ads_eligible='false',
                   listing_has_variations='false', variant_dict='')
        if counts[pid] > 1:
            meta = options.get(vid)
            if not meta or meta['product_id'] != pid or not meta['options']:
                raise ValueError('Missing verified Shopify option definitions for ' + ident)
            if not all(isinstance(k,str) and k and isinstance(v,str) and v for k,v in meta['options'].items()):
                raise ValueError('Invalid variant selection')
            signature = json.dumps(meta['options'],sort_keys=True,ensure_ascii=False)
            if signature in combinations[pid]:
                raise ValueError('Duplicate variant option combination')
            combinations[pid].add(signature)
            row.update(listing_has_variations='true', variant_dict=signature)
        gtin = field('gtin')
        if gtin and valid_gtin(gtin): row['gtin'] = gtin
        elif gtin: omitted_gtins.append(ident)
        secondary = [e.text for e in item.findall(G+'additional_image_link') if e.text]
        if secondary: row['additional_image_urls'] = ','.join(u.replace(',', '%2C') for u in secondary)
        if not all(row.get(k) for k in REQUIRED):
            raise ValueError('Missing required discovery fields')
        rows.append(row)
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    result = output.getvalue().encode('utf-8')
    if len(list(csv.DictReader(io.StringIO(result.decode('utf-8'))))) != len(items):
        raise ValueError('CSV round-trip lost rows')
    return result, {'offers':len(rows), 'products':len(counts),
                    'variant_groups':sum(n>1 for n in counts.values()),
                    'invalid_source_gtins_omitted':omitted_gtins}


if __name__ == '__main__':
    markets = json.loads((ROOT/'scripts/chatgpt-markets.json').read_text())
    locales = json.loads((ROOT/'scripts/chatgpt-locales.json').read_text())
    options = json.loads((ROOT/'scripts/chatgpt-variant-options.json').read_text())
    rows, stats = [], {}
    for country,currency in sorted(markets.items()):
        part, stats[country] = build(localized_source(country,locales.get(country)),options,country,currency)
        rows.extend(csv.DictReader(io.StringIO(part.decode())))
    if len({r['item_id'] for r in rows}) != len(rows):
        raise ValueError('Cross-market identity collision')
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output,fieldnames=FIELDS,lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    result = output.getvalue().encode('utf-8')
    target = ROOT/'almighty-tools-chatgpt.csv'
    temporary = target.with_suffix('.csv.tmp')
    temporary.write_bytes(result)
    temporary.replace(target)
    print(json.dumps({'offers':len(rows),'countries':len(stats),'currencies':sorted(set(markets.values())),'by_country':stats}))
