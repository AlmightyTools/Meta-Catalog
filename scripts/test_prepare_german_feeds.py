"""Safety and country/variant correctness of isolated German preparation."""
import unittest
import xml.etree.ElementTree as ET
from prepare_german_feeds import build_country, german_link, quote_fields, meta_country_language, G


class PreparationTests(unittest.TestCase):
    def fixture(self, pid='42'):
        raw = ('<rss xmlns:g="http://base.google.com/ns/1.0"><channel><title>Old</title>'
               '<description>English</description><item><g:id>Shopify_'+pid+'_7</g:id>'
               '<g:item_group_id>'+pid+'</g:item_group_id><title>English</title>'
               '<description>English</description><link>https://almighty.tools/products/test?variant=7&amp;country=DE</link>'
               '<g:image_link>https://almighty.tools/original-blue.jpg</g:image_link>'
               '<g:price>999.00 EUR</g:price><g:sale_price>998.00 EUR</g:sale_price>'
               '<g:availability>in stock</g:availability><g:color>Blue</g:color></item></channel></rss>').encode()
        pages={'/products/test':{'http':200,'lang':'de','description':'Deutsche Beschreibung',
                                'title':'Werkzeug','images':['https://almighty.tools/media/localized/de/test.webp']}}
        quotes={'test':{'http':200,'variants':{'7':{'price':{'amount':'12.34','currencyCode':'EUR'},
                                                  'compareAtPrice':{'amount':'20','currencyCode':'EUR'},
                                                  'availableForSale':False}}}}
        return raw,pages,quotes

    def test_exact_context_price_stock_and_variant_are_preserved(self):
        raw,pages,quotes=self.fixture()
        actual,excluded,review=build_country(raw,'CH',pages,quotes)
        item=ET.fromstring(actual).find('./channel/item')
        self.assertEqual(item.findtext(G+'price'),'20.00 EUR')
        self.assertEqual(item.findtext(G+'sale_price'),'12.34 EUR')
        self.assertEqual(item.findtext(G+'availability'),'out of stock')
        self.assertEqual(item.findtext(G+'color'),'Blau')
        self.assertIn('/de/products/test?variant=7&country=CH&currency=EUR',item.findtext('link'))
        self.assertEqual(item.findtext(G+'image_link'),'https://almighty.tools/original-blue.jpg')
        self.assertEqual(len(review),1)
        self.assertEqual(excluded,[])

    def test_combined_meta_urls_keep_country_variant_without_overriding_stock(self):
        raw,pages,quotes=self.fixture()
        catalogs={}
        for country in ('DE','AT','CH'):
            prepared,_,_=build_country(raw,country,pages,quotes)
            item=ET.fromstring(prepared).find('./channel/item')
            catalogs[country]={'Shopify_42_7':item}
        combined=meta_country_language(catalogs)
        self.assertEqual(len(combined),3)
        for row,country in zip(combined,('DE','AT','CH')):
            self.assertEqual(set(row),{'id','override','url'})
            self.assertEqual(row['id'],'7')
            self.assertEqual(row['override'],'de_XX|'+country)
            self.assertIn('variant=7&country='+country+'&currency=EUR',row['url'])
            self.assertIn('/de/products/test?',row['url'])

    def test_steam_is_never_invented_as_available(self):
        raw,pages,quotes=self.fixture('10180583522600')
        actual,excluded,_=build_country(raw,'DE',pages,quotes)
        self.assertEqual(ET.fromstring(actual).findall('./channel/item'),[])
        self.assertEqual(len(excluded),1)

    def test_missing_variant_has_no_fallback(self):
        raw,pages,quotes=self.fixture()
        quotes['test']['variants']={}
        actual,excluded,_=build_country(raw,'DE',pages,quotes)
        self.assertEqual(ET.fromstring(actual).findall('./channel/item'),[])
        self.assertEqual(len(excluded),1)

    def test_invalid_currency_and_url_are_rejected(self):
        with self.assertRaises(ValueError):
            quote_fields({'price':{'amount':'1','currencyCode':'USD'}})
        with self.assertRaises(ValueError):
            german_link('https://untrusted.example/products/x?variant=7','DE')
        with self.assertRaises(ValueError):
            german_link('https://almighty.tools/products/x','DE')

    def test_localized_image_must_match_exact_variant_product(self):
        raw,pages,quotes=self.fixture()
        mapping={'7':{'handle':'test','localized_url':'https://almighty.tools/media/localized/de/blue.webp'}}
        actual,_,_=build_country(raw,'DE',pages,quotes,mapping)
        self.assertEqual(ET.fromstring(actual).find('./channel/item').findtext(G+'image_link'),mapping['7']['localized_url'])
        mapping['7']['handle']='wrong-product'
        with self.assertRaisesRegex(ValueError,'identity'):
            build_country(raw,'DE',pages,quotes,mapping)


if __name__=='__main__': unittest.main()
