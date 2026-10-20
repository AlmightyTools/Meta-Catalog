import unittest
from pathlib import Path
import xml.etree.ElementTree as ET
from build_axon_feed import build_items, select_shopify_image, NS

SOURCE = Path(__file__).resolve().parents[1] / 'almighty-tools-gmc-us.xml'
IMAGE = 'https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/images/axon/test.png'


class FeedSafety(unittest.TestCase):
    def test_variant_color_photo_precedes_generic_cover(self):
        product = {'id': 1, 'featured_image': '//cdn.shopify.com/yellow.jpg',
                   'variants': [{'id': 2, 'featured_image': {'product_id':1, 'src':'https://cdn.shopify.com/blue.jpg'}}]}
        result = select_shopify_image(product, '1', '2')
        self.assertEqual(result['source_url'], 'https://cdn.shopify.com/blue.jpg')

    def test_product_first_image_without_variant_photo(self):
        product = {'id': 1, 'featured_image': '//cdn.shopify.com/cover.jpg',
                   'variants': [{'id': 2, 'featured_image': None}]}
        self.assertEqual(select_shopify_image(product, '1', '2')['source_url'], 'https://cdn.shopify.com/cover.jpg')

    def test_wrong_product_and_missing_variant_stop_publication(self):
        product = {'id': 1, 'featured_image': '//cdn.shopify.com/cover.jpg', 'variants': []}
        with self.assertRaises(AssertionError): select_shopify_image(product, '9', '2')
        with self.assertRaises(AssertionError): select_shopify_image(product, '1', '2')

    def source(self):
        return ET.fromstring(SOURCE.read_bytes())

    def build(self, root):
        return build_items(ET.tostring(root), lambda _: IMAGE)

    def test_current_price_and_numeric_identity(self):
        root = self.source()
        item = root.find('.//item')
        item.find('g:price', NS).text = '100.00 USD'
        sale = item.find('g:sale_price', NS)
        if sale is None:
            sale = ET.SubElement(item, '{' + NS['g'] + '}sale_price')
        sale.text = '60.00 USD'
        rows = self.build(root)
        self.assertEqual(rows[0]['price'], '60.00')
        self.assertEqual(rows[0]['id'], item.findtext('g:id', namespaces=NS).rsplit('_', 1)[1])
        self.assertEqual(rows[0]['itemId'], item.findtext('g:item_group_id', namespaces=NS))
        self.assertNotIn('salePriceStartDate', rows[0])
        self.assertTrue(all(',' not in r['description'] for r in rows))

    def test_checkout_domain_rejected(self):
        root = self.source()
        link = root.find('.//item/link')
        link.text = link.text.replace('almighty.tools', 'checkout.almighty.tools')
        with self.assertRaises(AssertionError): self.build(root)

    def test_wrong_selected_variant_rejected(self):
        root = self.source()
        root.find('.//item/link').text += '&variant=999'
        with self.assertRaises(AssertionError): self.build(root)

    def test_wrong_currency_rejected(self):
        root = self.source()
        root.find('.//item/g:price', NS).text = '100.00 GBP'
        with self.assertRaises(AssertionError): self.build(root)

    def test_partial_source_rejected(self):
        root = self.source()
        channel = root.find('channel')
        for item in channel.findall('item')[1:]: channel.remove(item)
        with self.assertRaises(AssertionError): self.build(root)


if __name__ == '__main__': unittest.main()
