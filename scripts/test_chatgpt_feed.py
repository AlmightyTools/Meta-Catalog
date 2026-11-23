"""Validate full market coverage, identity isolation, currency and source parity."""
import csv
import io
import json
import unittest
from pathlib import Path
from build_chatgpt_feed import build, localized_source, ROOT


class CatalogTests(unittest.TestCase):
    def test_all_markets_exact_source_parity(self):
        markets = json.loads((ROOT/'scripts/chatgpt-markets.json').read_text())
        locales = json.loads((ROOT/'scripts/chatgpt-locales.json').read_text())
        options = json.loads((ROOT/'scripts/chatgpt-variant-options.json').read_text())
        rows = list(csv.DictReader(io.StringIO((ROOT/'almighty-tools-chatgpt.csv').read_text())))
        self.assertEqual(len(markets),30)
        self.assertEqual({json.loads(r['target_countries'])[0] for r in rows},set(markets))
        self.assertEqual({r['price'].split()[-1] for r in rows},set(markets.values()))
        self.assertEqual(len({r['item_id'] for r in rows}),len(rows))
        for country,currency in markets.items():
            expected,_ = build(localized_source(country,locales.get(country)),options,country,currency)
            self.assertEqual([r for r in rows if json.loads(r['target_countries'])==[country]],list(csv.DictReader(io.StringIO(expected.decode()))))
            for row in (r for r in rows if json.loads(r['target_countries'])==[country]):
                if country in locales: self.assertIn('/'+locales[country]+'/products/',row['url'])

    def test_wrong_market_currency_rejected(self):
        options = json.loads((ROOT/'scripts/chatgpt-variant-options.json').read_text())
        raw = (ROOT/'almighty-tools-gmc-us.xml').read_bytes()
        with self.assertRaisesRegex(ValueError,'currency'):
            build(raw,options,'US','EUR')

    def test_missing_real_variant_definition_rejected(self):
        with self.assertRaisesRegex(ValueError,'option definitions'):
            build((ROOT/'almighty-tools-gmc-us.xml').read_bytes(),{})



    def test_regional_steam_variant_matrix_and_actual_stock(self):
        import copy
        import xml.etree.ElementTree as ET
        from urllib.parse import urlencode
        options = json.loads((ROOT/'scripts/chatgpt-variant-options.json').read_text())
        markets = json.loads((ROOT/'scripts/chatgpt-markets.json').read_text())
        locales = json.loads((ROOT/'scripts/chatgpt-locales.json').read_text())
        matrix = {**dict.fromkeys(['US','CA','MX','CO'],'51523663364392'),
                  **dict.fromkeys(['AU','NZ'],'68258444476712'),
                  **dict.fromkeys(['AT','BE','DE','ES','FI','FR','GR','NL','NO','PT','SE'],'68258444509480')}
        g='{http://base.google.com/ns/1.0}'
        steam=next(i for i in ET.fromstring((ROOT/'almighty-tools-gmc-us.xml').read_bytes()).findall('./channel/item') if i.findtext(g+'item_group_id')=='10180583522600')
        for country,currency in markets.items():
            for stock in ['in stock','out of stock']:
                tree=ET.fromstring(localized_source(country,locales.get(country)))
                channel=tree.find('channel')
                for item in list(channel.findall('item')):
                    if item.findtext(g+'item_group_id')=='10180583522600': channel.remove(item)
                baseline,_=build(ET.tostring(tree),options,country,currency)
                baseline=list(csv.DictReader(io.StringIO(baseline.decode())))
                for vid in ['51523663364392','68258444476712','68258444509480']:
                    item=copy.deepcopy(steam)
                    item.find(g+'id').text='Shopify_10180583522600_'+vid
                    locale='/'+locales[country] if country in locales else ''
                    item.find('link').text='https://almighty.tools'+locale+'/products/the-almighty-steam-cleaner?'+urlencode({'variant':vid,'country':country,'currency':currency})
                    item.find(g+'price').text='156.50 '+currency
                    sale=item.find(g+'sale_price')
                    if sale is not None: sale.text='93.90 '+currency
                    item.find(g+'availability').text=stock
                    channel.append(item)
                actual,_=build(ET.tostring(tree),options,country,currency)
                rows=list(csv.DictReader(io.StringIO(actual.decode())))
                selected=[r for r in rows if r['group_id']==country+'_10180583522600']
                self.assertEqual([r for r in rows if r not in selected],baseline,country)
                self.assertEqual(len(selected),int(country in matrix),country)
                if selected:
                    self.assertTrue(selected[0]['item_id'].endswith('_'+matrix[country]))
                    self.assertEqual(selected[0]['availability'],stock.replace(' ','_'))

    def test_allowed_steam_retains_actual_out_of_stock(self):
        import xml.etree.ElementTree as ET
        options = json.loads((ROOT/"scripts/chatgpt-variant-options.json").read_text())
        raw=ET.fromstring((ROOT/"almighty-tools-gmc-us.xml").read_bytes())
        g="{http://base.google.com/ns/1.0}"
        steam=next(i for i in raw.findall("./channel/item") if i.findtext(g+"item_group_id")=="10180583522600")
        steam.find(g+"availability").text="out of stock"
        result,_=build(ET.tostring(raw),options,"US","USD")
        row=next(r for r in csv.DictReader(io.StringIO(result.decode())) if r["group_id"]=="US_10180583522600")
        self.assertEqual(row["availability"],"out_of_stock")


if __name__=='__main__': unittest.main()
