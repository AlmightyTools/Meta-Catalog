"""Persist the owner's 2026-11-19 nominal-voltage confirmation for six models.

Owner confirmed remaining electric screwdrivers are 3.7 V. Cordless keeps its
documented 3.6 V; BitMaster already has documented 3.7 V. Do not touch the manual
180-in-1 variant or confuse Bolt's separate motor-rating attribute with battery voltage.
"""
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
G = '{http://base.google.com/ns/1.0}'
PRODUCTS = {'9346621047080','9576205058344','9737186672936','10146888024360','9790950277416','9864428290344'}
MANUAL = '51411044172072'
LABELS = {
    'en': ('Technical specifications','Nominal battery voltage'),
    'es': ('Especificaciones técnicas','Tensión nominal de la batería'),
    'fr': ('Caractéristiques techniques','Tension nominale de la batterie'),
}
VOLT_NAMES = {v[1] for v in LABELS.values()}


def strip_voltage(text):
    def remove(m):
        node=ET.fromstring(m[0].replace('<g:product_detail>','<g:product_detail xmlns:g="http://base.google.com/ns/1.0">',1))
        return '' if node.findtext(G+'attribute_name') in VOLT_NAMES else m[0]
    return re.sub(r'<g:product_detail>.*?</g:product_detail>',remove,text,flags=re.S)


def normalize(raw,locale='en'):
    source=raw.decode()
    section,label=LABELS[locale]
    count=0
    def convert(m):
        nonlocal count
        original=m[0]
        node=ET.fromstring(original.replace('<item>','<item xmlns:g="http://base.google.com/ns/1.0">',1))
        ident=node.findtext(G+'id') or ''
        ids=re.fullmatch(r'(?:Shopify_|shopify_(?:AU|NZ)_|dup_US_)(\d+)_(\d+)',ident)
        if not ids or ids[1] not in PRODUCTS or ids[2]==MANUAL:return original
        existing=[d.findtext(G+'attribute_value') for d in node.findall(G+'product_detail') if d.findtext(G+'attribute_name') in VOLT_NAMES]
        if existing:
            if existing!=['3.7 V']:raise ValueError('Conflicting nominal voltage: '+ident)
            return original
        detail='<g:product_detail><g:section_name>'+section+'</g:section_name><g:attribute_name>'+label+'</g:attribute_name><g:attribute_value>3.7 V</g:attribute_value></g:product_detail>'
        count+=1
        return original.replace('</item>',detail+'</item>')
    output=re.sub(r'<item>.*?</item>',convert,source,flags=re.S)
    ET.fromstring(output)
    if strip_voltage(output)!=strip_voltage(source):raise ValueError('Non-voltage field changed')
    return output.encode(),count


if __name__=='__main__':
    candidates={}
    counts={}
    for path in sorted(ROOT.glob('almighty-tools-gmc-*.xml')):
        locale='es' if path.stem.endswith('-es') else 'fr' if path.stem.endswith('-fr') else 'en'
        raw=path.read_bytes()
        output,count=normalize(raw,locale)
        counts[path.name]=count
        if output!=raw:candidates[path]=output
    for path,output in candidates.items():
        temp=path.with_suffix('.xml.tmp');temp.write_bytes(output);temp.replace(path)
    print(json.dumps({'feeds':len(candidates),'nominal_voltage_records_added':sum(counts.values())}))
