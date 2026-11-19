"""Reuse real published German product copy; do not invent translated claims."""
import concurrent.futures
import json
import urllib.request
import subprocess
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urlsplit
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Schema(HTMLParser):
    def __init__(self):
        super().__init__()
        self.schema = False
        self.parts = []
        self.lang = None
    def handle_starttag(self,tag,attrs):
        attrs = dict(attrs)
        if tag == 'html': self.lang = attrs.get('lang')
        if tag == 'script': self.schema = attrs.get('type')=='application/ld+json'
    def handle_endtag(self,tag):
        if tag == 'script': self.schema = False
    def handle_data(self,data):
        if self.schema: self.parts.append(data)


def fetch(path):
    url = 'https://almighty.tools/de'+path
    response = subprocess.run(['curl','--fail','--silent','--show-error','--max-time','45',url],capture_output=True,check=True)
    parser = Schema()
    parser.feed(response.stdout.decode())
    if parser.lang != 'de': raise ValueError('Wrong published German language')
    products = [json.loads(s) for s in parser.parts if s.strip()]
    products = [s for s in products if s.get('@type')=='Product']
    if len(products)!=1: raise ValueError('Missing German product schema: '+path)
    p = products[0]
    if not p.get('name') or not p.get('description'): raise ValueError('Missing German product copy')
    return path, {'title':p['name'],'description':p['description'],'url':url}


if __name__=='__main__':
    paths = sorted({urlsplit(i.findtext('link')).path for i in ET.parse(ROOT/'almighty-tools-gmc-de.xml').findall('./channel/item')})
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        result = dict(pool.map(fetch,paths))
    target = ROOT/'scripts/chatgpt-german-copy.json'
    temp = target.with_suffix('.json.tmp')
    temp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    temp.replace(target)
    print('Verified published German product pages:',len(result))
