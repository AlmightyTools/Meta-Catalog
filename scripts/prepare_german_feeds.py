"""Prepare isolated German candidates. Never publish or register a provider source."""
import argparse
import copy
import csv
import hashlib
import io
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlencode, urlsplit, urlunsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
G = '{http://base.google.com/ns/1.0}'
MARKETS = ('DE', 'AT', 'CH')
STEAM = '10180583522600'
ET.register_namespace('g', G[1:-1])


def csv_bytes(rows, fields):
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode()


def rows(raw):
    return list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))


def copy_field(item, name):
    return item.findtext(G+'structured_'+name+'/'+G+'content') or item.findtext(name) or item.findtext(G+name)


def quote_fields(variant, currency='EUR'):
    price = variant['price']
    if price['currencyCode'] != currency or Decimal(price['amount']) <= 0:
        raise ValueError('Invalid contextual price/currency')
    current = Decimal(price['amount'])
    compare = variant.get('compareAtPrice')
    if compare and compare['currencyCode'] != currency:
        raise ValueError('Invalid contextual compare-at currency')
    regular = max(current, Decimal(compare['amount'])) if compare else current
    return (f'{regular:.2f} {currency}',
            f'{current:.2f} {currency}' if regular > current else '',
            'in stock' if variant['availableForSale'] else 'out of stock')


def german_link(link, country):
    parsed = urlsplit(link)
    if parsed.scheme != 'https' or parsed.hostname != 'almighty.tools':
        raise ValueError('Untrusted product URL')
    path = parsed.path if parsed.path.startswith('/de/products/') else '/de' + parsed.path
    query = parse_qs(parsed.query)
    if not query.get('variant') or len(query['variant']) != 1:
        raise ValueError('Missing exact variant')
    query.update(country=[country], currency=['EUR'])
    return urlunsplit(parsed._replace(path=path, query=urlencode(query, doseq=True)))


def build_country(raw, country, pages, quotes, image_mapping=None):
    tree = ET.fromstring(raw)
    channel = tree.find('channel')
    counts = Counter(i.findtext(G+'item_group_id') for i in channel.findall('item'))
    output, exclusions, image_review = [], [], []
    for original in channel.findall('item'):
        pid = original.findtext(G+'item_group_id')
        ident = original.findtext(G+'id')
        path = unquote(urlsplit(original.findtext('link')).path)
        handle = path.split('/products/')[-1]
        vid = ident.rsplit('_', 1)[-1]
        market = quotes.get(handle)
        if pid == STEAM or not market or market['http'] != 200 or vid not in market['variants']:
            exclusions.append({'id': ident, 'reason': 'Steam regional launch not verified' if pid == STEAM else 'No exact contextual variant'})
            continue
        page = pages[path]
        if page['http'] != 200 or page['lang'] != 'de' or not page['description'] or not page['images']:
            raise ValueError('Unverified German product content: '+path)
        item = copy.deepcopy(original)
        # Avoid exporting old English prose under a German language declaration.
        for node in list(item):
            if node.tag.split('}')[-1] in {'title','structured_title','description','structured_description','product_detail','product_highlight','additional_image_link','product_type'}:
                item.remove(node)
        for name, value, limit in [('title',page['title'],150), ('description',page['description'],5000)]:
            structured = original.find(G+'structured_'+name)
            if structured is not None:
                structured = copy.deepcopy(structured)
                structured.find(G+'content').text = value[:limit]
                item.append(structured)
            else:
                ET.SubElement(item, name).text = value[:limit]
        colors = {'Blue':'Blau', 'Yellow':'Gelb', 'Pink':'Rosa', 'Black':'Schwarz',
                  'White':'Weiß', 'Green':'Grün', 'Red':'Rot', 'Silver':'Silber',
                  'Grey':'Grau', 'Gray':'Grau', 'Orange':'Orange'}
        for field in ('color', 'size'):
            node = item.find(G+field)
            if node is not None and node.text in colors:
                node.text = colors[node.text]
        item.find('link').text = german_link(original.findtext('link'), country)
        regular, sale, stock = quote_fields(market['variants'][vid])
        item.find(G+'price').text = regular
        prior_sale = item.find(G+'sale_price')
        if prior_sale is not None:
            item.remove(prior_sale)
        if sale:
            ET.SubElement(item, G+'sale_price').text = sale
        item.find(G+'availability').text = stock
        # Retain approved exact-variant primary photos until German artwork has
        # a channel-policy AND variant-identity review; never substitute colors.
        image_review.append({'id': ident, 'current_primary': original.findtext(G+'image_link'),
                             'localized_product_candidate': page['images'][0],
                             'multiple_variants': counts[pid] > 1,
                             'status': 'localized image mapping/policy approval pending'})
        mapped = (image_mapping or {}).get(vid)
        if mapped:
            url = urlsplit(mapped['localized_url'])
            if mapped['handle'] != handle or url.hostname != 'almighty.tools' or not url.path.startswith('/media/localized/de/'):
                raise ValueError('Localized variant image identity mismatch')
            item.find(G+'image_link').text = mapped['localized_url']
            image_review[-1].update(status='exact variant source mapped; channel image-policy review pending',
                                    localized_product_candidate=mapped['localized_url'])
        output.append(item)
    for item in list(channel.findall('item')):
        channel.remove(item)
    for item in output:
        channel.append(item)
    channel.find('title').text = 'Almighty Tools - Deutsch - '+country
    channel.find('description').text = 'Deutscher Produktkatalog - EUR - '+country
    return ET.tostring(tree, encoding='utf-8', xml_declaration=True), exclusions, image_review


def prepare(evidence, output):
    evidence, output = Path(evidence), Path(output).resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError('Candidates must stay outside the live repository checkout')
    pages = json.loads((evidence/'german-pages.json').read_text())
    quotes = json.loads((evidence/'market-quotes.json').read_text())
    image_mapping = json.loads((evidence/'exact-localized-variant-images.json').read_text())
    artifacts, manifest, by_id = {}, {}, {}
    for country in MARKETS:
        name = 'almighty-tools-gmc-'+country.lower()+'-de.xml'
        raw, excluded, review = build_country((ROOT/('almighty-tools-gmc-'+country.lower()+'.xml')).read_bytes(), country, pages, quotes[country], image_mapping)
        artifacts[name] = raw
        # Microsoft candidate uses the same XML data contract, separately gated.
        ms = ET.fromstring(raw)
        for offer in ms.findall('./channel/item'):
            offer.find(G+'id').text = offer.findtext(G+'id').rsplit('_',1)[-1]
            for name in ('title', 'description'):
                value = copy_field(offer, name)
                structured = offer.find(G+'structured_'+name)
                if structured is not None:
                    offer.remove(structured)
                    ET.SubElement(offer, name).text = value
        artifacts['microsoft-ads-'+country.lower()+'-de.xml'] = ET.tostring(ms, encoding='utf-8', xml_declaration=True)
        items = ET.fromstring(raw).findall('./channel/item')
        if len({i.findtext(G+'id') for i in items}) != len(items):
            raise ValueError('Duplicate German offer identity')
        by_id[country] = {i.findtext(G+'id'): i for i in items}
        manifest[country] = {'language': 'de', 'currency': 'EUR', 'offers': len(items),
                             'products': len({i.findtext(G+'item_group_id') for i in items}),
                             'exclusions': excluded, 'image_review': review}
    # Stage a separate German language overlay, keeping the existing ES/FR
    # source untouched. Do not guess country/language link override precedence.
    originals = rows((ROOT/'language-feed.csv').read_bytes())
    language = []
    for ident, item in by_id['DE'].items():
        language.append({'id': ident.rsplit('_',1)[-1], 'override': 'de_XX',
                         'title': copy_field(item,'title'), 'description': copy_field(item,'description'),
                         'image_link':item.findtext(G+'image_link')})
    artifacts['meta-language-de-candidate.csv'] = csv_bytes(language, ['id','override','title','description','image_link'])
    discovery = rows((ROOT/'almighty-tools-chatgpt.csv').read_bytes())
    fields = list(discovery[0])
    staged, changed, omitted = [], 0, []
    for source in discovery:
        country = json.loads(source['target_countries'])[0]
        if country not in MARKETS:
            staged.append(source)
            continue
        canonical = 'Shopify_' + source['item_id'].split('_', 2)[-1]
        item = by_id[country].get(canonical)
        if item is None:
            omitted.append(source['item_id'])
            continue
        row = dict(source, title=copy_field(item,'title'), description=copy_field(item,'description'),
                   url=item.findtext('link'), price=item.findtext(G+'price'),
                   sale_price=item.findtext(G+'sale_price') or '',
                   image_url=item.findtext(G+'image_link'),
                   availability=item.findtext(G+'availability').replace(' ', '_'))
        changed += row != source
        staged.append(row)
    artifacts['almighty-tools-chatgpt-german-candidate.csv'] = csv_bytes(staged, fields)
    assert [r for r in staged if json.loads(r['target_countries'])[0] not in MARKETS] == [r for r in discovery if json.loads(r['target_countries'])[0] not in MARKETS]
    blockers = ['German index release not verified; source pages currently noindex',
                'German landing and checkout market/language/price readback required',
                'Localized exact-variant images require policy and identity review',
                'Meta country/language link and image precedence must be verified before registration',
                'Microsoft DE/AT/CH catalog targets not independently confirmed']
    summary = {'status': 'PREPARED_NOT_ACTIVATED', 'activation_ready': False,
               'evidence_collected_at': json.loads((evidence/'collection-proof.json').read_text())['checked_at_utc'],
               'countries': manifest, 'blockers': blockers,
               'meta': {'existing_language_rows_preserved':len(originals), 'german_rows':len(language), 'country_feed_unchanged':True, 'stock_not_overridden':True, 'language_url_override':'not emitted until country/language precedence is verified'},
               'openai': {'total_rows':len(staged), 'changed_german_rows':changed, 'omitted':omitted, 'other_country_rows_unchanged':True},
               'excluded_systems': {'Axon':'Current catalog explicitly US/USD; no approved German catalog scope', 'Reviews':'Not a product-offer export; no invented translated reviews'},
               'files': {name:hashlib.sha256(raw).hexdigest() for name,raw in artifacts.items()}}
    output.mkdir(parents=True, exist_ok=True)
    for name, raw in artifacts.items():
        (output/name).write_bytes(raw)
    (output/'manifest.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
    return summary


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--evidence', required=True)
    cli.add_argument('--output', required=True)
    args = cli.parse_args()
    result = prepare(args.evidence, args.output)
    print(json.dumps({'status':result['status'], 'countries':{k:v['offers'] for k,v in result['countries'].items()}, 'files':len(result['files']), 'activation_ready':False}))
