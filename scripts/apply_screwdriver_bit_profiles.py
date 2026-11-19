"""Copy verified Bolt/Wizard Wand bit families from the merchant's live pages.

Verified 2026-11-19:
Bolt: What's Included plus The_Almighty_Bolt_006.webp, v=1761584676.
Wizard Wand: The_Almighty_Wizard_Wand_005.webp, v=1760359955,
linked from https://almighty.tools/products/the-almighty-wizard-wand.
Only clearly labeled profiles are included; no guessed accessory counts or lengths.
"""
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
G='{http://base.google.com/ns/1.0}'
PROFILES={
    '9864428290344':'Phillips; Slotted; Hex; Torx; Pozidriv; Square; Pentalobe',
    '9790950277416':'Phillips; Slotted; Hex; Torx; Security Torx; Pentalobe; Y-type (Y0.6, Y1)',
}
LABELS={
    'en':('Technical specifications','Bit/Head Type'),
    'es':('Especificaciones técnicas','Tipo de punta'),
    'fr':('Caractéristiques techniques','Type d’embout'),
}
BIT_NAMES={v[1] for v in LABELS.values()}


def strip_profiles(text):
    def remove(m):
        node=ET.fromstring(m[0].replace('<g:product_detail>','<g:product_detail xmlns:g="http://base.google.com/ns/1.0">',1))
        return '' if node.findtext(G+'attribute_name') in BIT_NAMES else m[0]
    return re.sub(r'<g:product_detail>.*?</g:product_detail>',remove,text,flags=re.S)


def normalize(raw,locale='en'):
    source=raw.decode()
    count=0
    def convert(m):
        nonlocal count
        original=m[0]
        item=ET.fromstring(original.replace('<item>','<item xmlns:g="http://base.google.com/ns/1.0">',1))
        ident=item.findtext(G+'id') or ''
        ids=re.fullmatch(r'(?:Shopify_|shopify_(?:AU|NZ)_|dup_US_)(\d+)_(\d+)',ident)
        if not ids or ids[1] not in PROFILES:return original
        value=PROFILES[ids[1]]
        existing=[d.findtext(G+'attribute_value') for d in item.findall(G+'product_detail') if d.findtext(G+'attribute_name') in BIT_NAMES]
        if existing:
            if existing!=[value]:raise ValueError('Conflicting bit-profile record: '+ident)
            return original
        section,label=LABELS[locale]
        detail='<g:product_detail><g:section_name>'+section+'</g:section_name><g:attribute_name>'+label+'</g:attribute_name><g:attribute_value>'+value+'</g:attribute_value></g:product_detail>'
        count+=1
        return original.replace('</item>',detail+'</item>')
    result=re.sub(r'<item>.*?</item>',convert,source,flags=re.S)
    ET.fromstring(result)
    if strip_profiles(result)!=strip_profiles(source):raise ValueError('Non-profile fields changed')
    return result.encode(),count


if __name__=='__main__':
    candidates={}
    total=0
    for path in ROOT.glob('almighty-tools-gmc-*.xml'):
        locale='es' if path.stem.endswith('-es') else 'fr' if path.stem.endswith('-fr') else 'en'
        raw=path.read_bytes();result,count=normalize(raw,locale);total+=count
        if result!=raw:candidates[path]=result
    for path,result in candidates.items():
        temp=path.with_suffix('.xml.tmp');temp.write_bytes(result);temp.replace(path)
    print(json.dumps({'feeds':len(candidates),'bit_profile_records_added':total}))
