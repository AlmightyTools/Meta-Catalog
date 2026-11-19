"""Include source-verified bit profiles and nominal voltage in description text.

Reuse the verified technical attributes; never infer battery voltage from USB input,
motor marketing ratings, battery chemistry or a similar product.
"""
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
G = '{http://base.google.com/ns/1.0}'
TARGETS = {
    '9346606301480': '3.6 V',
    '9346621047080': '3.7 V',
    '9576205058344': '3.7 V',
    '9811758580008': '3.7 V',
    '9737186672936': '3.7 V',
    '10146888024360': '3.7 V',
    '9790950277416': '3.7 V',
    '9864428290344': '3.7 V',
}
MANUAL_VARIANT = '51411044172072'
LABELS = {
    'en': ('Technical specifications:', 'Bit/head types:', 'Nominal battery voltage:'),
    'es': ('Especificaciones técnicas:', 'Tipos de punta:', 'Tensión nominal de la batería:'),
    'fr': ('Caractéristiques techniques :', 'Types d’embout :', 'Tension nominale de la batterie :'),
}
BIT_LABELS = {'Bit/Head Type','Tipo de punta','Type d’embout'}
VOLT_LABELS = {'Nominal battery voltage','Tensión nominal de la batería','Tension nominale de la batterie'}


def strip_descriptions(text):
    return re.sub(r'<g:structured_description>.*?</g:structured_description>|<g:description>.*?</g:description>', '', text, flags=re.S)


def normalize(raw, locale='en'):
    source = raw.decode('utf-8')
    header, bit_label, voltage_label = LABELS[locale]
    count = 0
    def convert(match):
        nonlocal count
        original = match.group(0)
        item = ET.fromstring(original.replace('<item>','<item xmlns:g="http://base.google.com/ns/1.0">',1))
        ident = item.findtext(G+'id') or ''
        ids = re.fullmatch(r'(?:Shopify_|shopify_(?:AU|NZ)_|dup_US_)(\d+)_(\d+)',ident)
        if not ids or ids[1] not in TARGETS or ids[2] == MANUAL_VARIANT: return original
        details = {d.findtext(G+'attribute_name'):d.findtext(G+'attribute_value') for d in item.findall(G+'product_detail')}
        bits = [v for k,v in details.items() if k in BIT_LABELS]
        if (len(bits)!=1 or not bits[0]) and ids[1] not in {'9790950277416','9864428290344'}:
            raise ValueError('Missing verified bit types for '+ident)
        sentences = [header]+([bit_label+' '+bits[0]+'.'] if bits else [])
        old_suffix = ' '.join(sentences)
        voltage = TARGETS[ids[1]]
        if voltage:
            values = [v for k,v in details.items() if k in VOLT_LABELS]
            if values != [voltage]: raise ValueError('Verified nominal-voltage mismatch for '+ident)
            sentences.append(voltage_label+' '+voltage+'.')
        suffix = ' '.join(sentences)
        node = item.find(G+'structured_description/'+G+'content')
        structured = node is not None
        if node is None: node = item.find(G+'description')
        if node is None or not node.text: raise ValueError('Missing original description')
        text = node.text
        if header in text:
            if text.count(suffix)==1: return original
            if text.count(old_suffix)==1 and voltage_label not in text:
                new = text.replace(old_suffix,suffix,1)
            else:
                raise ValueError('Unexpected existing technical suffix; preserve for review')
        else:
            new = text.rstrip()+' '+suffix
        if len(new)>5000: raise ValueError('Description too long')
        if structured:
            pattern = r'(<g:structured_description>\s*(?:<g:digital_source_type>.*?</g:digital_source_type>\s*)?<g:content>).*?(</g:content>)'
        else:
            pattern = r'(<g:description>).*?(</g:description>)'
        output,n = re.subn(pattern,lambda m:m[1]+escape(new)+m[2],original,count=1,flags=re.S)
        if n!=1 or strip_descriptions(output)!=strip_descriptions(original):
            raise ValueError('Unexpected description structure or unrelated change')
        count += 1
        return output
    result = re.sub(r'<item>.*?</item>',convert,source,flags=re.S)
    ET.fromstring(result)
    if strip_descriptions(result)!=strip_descriptions(source):
        raise ValueError('Feed fields other than descriptions changed')
    return result.encode('utf-8'),count


def main():
    candidates, stats = {}, {}
    for path in sorted(ROOT.glob('almighty-tools-gmc-*.xml')):
        locale = 'es' if path.stem.endswith('-es') else 'fr' if path.stem.endswith('-fr') else 'en'
        raw = path.read_bytes()
        output,count = normalize(raw,locale)
        if output!=raw: candidates[path]=output
        stats[path.name]=count
    for path,output in candidates.items():
        temp = path.with_suffix('.xml.tmp')
        temp.write_bytes(output)
        temp.replace(path)
    print(json.dumps({'changed_feeds':len(candidates),'changed_descriptions':sum(stats.values()),'by_feed':stats}))


if __name__=='__main__': main()
