"""Get Qatar contextual prices from the same public Shopify API used by storefront.

No API keys or admin credentials. Refresh only the Qatar source for OpenAI.
Unpublished market products are omitted; truncated responses fail before replacement.
"""
import concurrent.futures
import json
import urllib.request
import xml.etree.ElementTree as ET
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit, parse_qs, urlencode, urlunsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
G = '{http://base.google.com/ns/1.0}'
ET.register_namespace('g','http://base.google.com/ns/1.0')


def fetch(handles):
    fields = 'handle variants(first:100){pageInfo{hasNextPage} nodes{id availableForSale price{amount currencyCode} compareAtPrice{amount currencyCode}}}'
    query = 'query OpenAIMarketPrices($country:CountryCode!,' + ','.join('$h'+str(i)+':String!' for i in range(len(handles))) + ') @inContext(country:$country){' + ' '.join('p'+str(i)+':product(handle:$h'+str(i)+'){'+fields+'}' for i in range(len(handles))) + '}'
    body = {'query':query,'variables':dict(country='QA',**{'h'+str(i):h for i,h in enumerate(handles)})}
    request = urllib.request.Request('https://checkout.almighty.tools/api/2026-07/graphql.json',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(request,timeout=45) as response:
        result = json.load(response)
    if result.get('errors'): raise ValueError('Public contextual pricing query failed')
    variants = {}
    for key,product in result['data'].items():
        if product is None:
            print('Not published in Qatar:',handles[int(key[1:])])
            continue
        if product['variants']['pageInfo']['hasNextPage']:
            raise ValueError('Truncated Qatar product')
        for v in product['variants']['nodes']:
            if v['price']['currencyCode'] != 'QAR': raise ValueError('Qatar currency mismatch')
            variants[v['id'].split('/')[-1]] = v
    return variants


def refresh():
    root = ET.parse(ROOT/'almighty-tools-gmc-us.xml')
    items = root.findall('./channel/item')
    handles = sorted({unquote(urlsplit(i.findtext('link')).path.split('/')[-1]) for i in items})
    batches = [handles[i:i+3] for i in range(0,len(handles),3)]
    prices = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for values in pool.map(fetch,batches): prices.update(values)
    if len(prices) < 100: raise ValueError('Incomplete Qatar catalog')
    included = 0
    for item in items:
        vid = item.findtext(G+'id').split('_')[-1]
        if vid not in prices:
            root.getroot().find('channel').remove(item)
            continue
        v = prices[vid]
        included += 1
        price, compare = v['price'],v.get('compareAtPrice')
        actual = Decimal(price['amount'])
        if actual <= 0: raise ValueError('Invalid Qatar price')
        discounted = compare and compare['currencyCode']=='QAR' and Decimal(compare['amount']) > actual
        item.find(G+'price').text = (compare['amount'] if discounted else price['amount'])+' QAR'
        sale = item.find(G+'sale_price')
        if discounted:
            if sale is None: sale = ET.SubElement(item,G+'sale_price')
            sale.text = price['amount']+' QAR'
        elif sale is not None: item.remove(sale)
        item.find(G+'availability').text = 'in stock' if v['availableForSale'] else 'out of stock'
        link = item.find('link')
        parsed = urlsplit(link.text)
        params = parse_qs(parsed.query)
        params['country'] = ['QA']
        link.text = urlunsplit(parsed._replace(query=urlencode(params,doseq=True)))
    target = ROOT/'scripts/chatgpt-qatar.xml'
    temp = target.with_suffix('.xml.tmp')
    root.write(temp,encoding='utf-8',xml_declaration=True)
    temp.replace(target)
    print('Verified public Shopify Qatar variants:',included)


if __name__ == '__main__': refresh()
