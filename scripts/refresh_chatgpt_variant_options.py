"""Refresh public Shopify variant definitions; never use this endpoint for market prices."""
import collections
import concurrent.futures
import json
import urllib.parse
import urllib.request
from feed_public_json import read_json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
G = '{http://base.google.com/ns/1.0}'


def get_options(entry):
    pid, items = entry
    if len(items) < 2: return {}
    path = urllib.parse.urlsplit(items[0].findtext('link')).path
    product = read_json('https://checkout.almighty.tools'+path+'.js', timeout=30)
    if str(product['id']) != pid: raise ValueError('Shopify product mismatch')
    names = [o['name'] for o in product['options']]
    variants = {str(v['id']):v for v in product['variants']}
    result = {}
    for item in items:
        vid = item.findtext(G+'id').split('_')[-1]
        variant = variants[vid]
        options = {name:variant['option'+str(i+1)] for i,name in enumerate(names)}
        if not options or not all(isinstance(v,str) and v for v in options.values()):
            raise ValueError('Missing variant option definition')
        result[vid] = {'product_id':pid,'options':options}
    return result


if __name__ == '__main__':
    groups = collections.defaultdict(list)
    for item in ET.parse(ROOT/'almighty-tools-gmc-us.xml').findall('./channel/item'):
        groups[item.findtext(G+'item_group_id')].append(item)
    result = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for part in pool.map(get_options,groups.items()): result.update(part)
    target = ROOT/'scripts/chatgpt-variant-options.json'
    temp = target.with_suffix('.json.tmp')
    temp.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    temp.replace(target)
    print('Verified Shopify variant definitions:',len(result))
