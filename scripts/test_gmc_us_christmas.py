#!/usr/bin/env python3
import copy
import unittest
import xml.etree.ElementTree as ET
from build_gmc_us_christmas import G, SOURCE, build

class ChristmasFeedTests(unittest.TestCase):
    def setUp(self):
        self.raw = SOURCE.read_bytes()

    def test_all_other_attributes_and_variants_preserved(self):
        output = build(self.raw)
        self.assertEqual(build(self.raw), output)
        source = ET.fromstring(self.raw).findall('./channel/item')
        target = ET.fromstring(output).findall('./channel/item')
        self.assertEqual(len(source), len(target))
        self.assertTrue(set(i.findtext(G+'id') for i in source).isdisjoint(i.findtext(G+'id') for i in target))
        mutable = {'id', 'item_group_id', 'structured_title', 'structured_description', 'custom_label_3', 'custom_label_4'}
        for old, new in zip(source, target):
            self.assertEqual(new.findtext(G+'id'), old.findtext(G+'id').replace('Shopify_', 'dup_US_', 1))
            self.assertEqual(new.findtext(G+'item_group_id'), 'dup_US_'+old.findtext(G+'item_group_id'))
            self.assertEqual(new.findtext(G+'custom_label_4'), 'dup')
            self.assertEqual(new.findtext(G+'custom_label_3'), 'christmas_gifts')
            self.assertTrue(new.findtext(G+'structured_title/'+G+'content').startswith('Gift for DIYer. '))
            self.assertTrue(new.findtext(G+'structured_description/'+G+'content').endswith('Ready to gift'))
            for field, limit in (('structured_title',150),('structured_description',5000)):
                value = new.findtext(G+field+'/'+G+'content')
                self.assertIn('Christmas gift', value.replace('Christmas Gift', 'Christmas gift'))
                self.assertLessEqual(len(value), limit)
                self.assertIn(old.findtext(G+field+'/'+G+'content'), value)
            def immutable(item):
                return [ET.tostring(e) for e in item if e.tag.removeprefix(G) not in mutable]
            self.assertEqual(immutable(old), immutable(new))

    def test_price_and_stock_follow_source(self):
        changed = self.raw.replace(b'199.99 USD', b'198.99 USD', 1).replace(b'<g:availability>in stock</g:availability>', b'<g:availability>out of stock</g:availability>', 1)
        first = ET.fromstring(build(changed)).find('./channel/item')
        self.assertEqual(first.findtext(G+'price'), '198.99 USD')
        self.assertEqual(first.findtext(G+'availability'), 'out of stock')

    def test_invalid_sources_are_rejected(self):
        for bad in (
            self.raw.replace(b'country=US',b'country=CA',1),
            self.raw.replace(b'199.99 USD',b'199.99 EUR',1),
            self.raw.replace(b'</item>',b'<g:custom_label_4>existing</g:custom_label_4></item>',1),
            self.raw.replace(b'<g:structured_title>',b'<g:title>conflict</g:title><g:structured_title>',1),
            b'<rss><channel/></rss>',
        ):
            with self.assertRaises(ValueError):
                build(bad)

if __name__ == '__main__':
    unittest.main()
