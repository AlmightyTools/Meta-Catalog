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


if __name__=='__main__': unittest.main()
