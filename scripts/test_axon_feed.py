import unittest
from unittest.mock import patch, MagicMock
import json
import tempfile
import urllib.error
from pathlib import Path
import xml.etree.ElementTree as ET
from build_axon_feed import build_items, select_shopify_image, shopify_images, shopify_product_payload, main, NS

SOURCE = Path(__file__).resolve().parents[1] / 'almighty-tools-gmc-us.xml'
IMAGE = 'https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/images/axon/test.png'


class FeedSafety(unittest.TestCase):
    def response(self, product=None, url='https://checkout.almighty.tools/products/tool.js'):
        response = MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = url
        response.read.return_value = json.dumps(product or {'id': 1}).encode()
        return response

    def test_temporary_gateway_error_recovers_with_bounded_retries(self):
        for code in (502, 503, 504):
            error = urllib.error.HTTPError('https://checkout.almighty.tools', code, 'temporary', {}, None)
            with self.subTest(code=code), patch('build_axon_feed.urllib.request.urlopen', side_effect=[error, error, self.response()]) as request, patch('build_axon_feed.time.sleep') as sleep:
                self.assertEqual(shopify_product_payload('request'), {'id': 1})
                self.assertEqual(request.call_count, 3)
                self.assertEqual([c.args[0] for c in sleep.call_args_list], [2, 4])

    def test_persistent_gateway_error_never_uses_previous_image_cache(self):
        error = urllib.error.HTTPError('https://checkout.almighty.tools', 503, 'temporary', {}, None)
        with patch('build_axon_feed.urllib.request.urlopen', side_effect=error) as request, patch('build_axon_feed.time.sleep'):
            with self.assertRaises(urllib.error.HTTPError):
                shopify_images(SOURCE.read_bytes(), {'unused': {'source_url': 'https://cdn.shopify.com/old.jpg'}})
            self.assertEqual(request.call_count, 3)

    def test_retry_after_is_respected_and_long_pause_stops_build(self):
        for value, expected_delay in [('7', 7), ('invalid', 2), ('Wed, 01 Jan 2020 00:00:00 GMT', 2)]:
            error = urllib.error.HTTPError('https://checkout.almighty.tools', 503, 'temporary', {'Retry-After': value}, None)
            with self.subTest(value=value), patch('build_axon_feed.urllib.request.urlopen', side_effect=[error, self.response()]), patch('build_axon_feed.time.sleep') as sleep:
                shopify_product_payload('request')
                sleep.assert_called_once_with(expected_delay)
        for value in ('120', 'nan', 'inf'):
            error = urllib.error.HTTPError('https://checkout.almighty.tools', 503, 'temporary', {'Retry-After': value}, None)
            with self.subTest(value=value), patch('build_axon_feed.urllib.request.urlopen', side_effect=error) as request, patch('build_axon_feed.time.sleep') as sleep:
                with self.assertRaises(urllib.error.HTTPError): shopify_product_payload('request')
                self.assertEqual(request.call_count, 1)
                sleep.assert_not_called()

    def test_nontransient_http_errors_are_not_retried(self):
        for code in (401, 403, 404, 429, 500):
            error = urllib.error.HTTPError('https://checkout.almighty.tools', code, 'stop', {}, None)
            with self.subTest(code=code), patch('build_axon_feed.urllib.request.urlopen', side_effect=error) as request, patch('build_axon_feed.time.sleep') as sleep:
                with self.assertRaises(urllib.error.HTTPError): shopify_product_payload('request')
                self.assertEqual(request.call_count, 1)
                sleep.assert_not_called()

    def test_invalid_json_and_redirect_still_stop_immediately(self):
        response = self.response()
        response.read.return_value = b'invalid'
        with patch('build_axon_feed.urllib.request.urlopen', return_value=response) as request:
            with self.assertRaises(json.JSONDecodeError): shopify_product_payload('request')
            self.assertEqual(request.call_count, 1)
        with patch('build_axon_feed.urllib.request.urlopen', return_value=self.response(url='https://example.com/tool.js')):
            with self.assertRaises(AssertionError): shopify_product_payload('request')

    def test_failed_refresh_preserves_all_published_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'scripts').mkdir()
            files = {'almighty-tools-gmc-us.xml': SOURCE.read_bytes(),
                     'almighty-tools-axon-us.csv': b'previous catalog\n',
                     'scripts/axon-image-cache.json': b'{}\n',
                     'scripts/axon-source-images.json': b'{}\n'}
            for path, data in files.items(): (root / path).write_bytes(data)
            error = urllib.error.HTTPError('https://checkout.almighty.tools', 503, 'temporary', {}, None)
            with patch('build_axon_feed.ROOT', root), patch('build_axon_feed.urllib.request.urlopen', side_effect=error), patch('build_axon_feed.time.sleep'):
                with self.assertRaises(urllib.error.HTTPError): main()
            self.assertEqual({path: (root / path).read_bytes() for path in files}, files)

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

    def test_rate_limit_preserves_verified_originals_and_stops_requests(self):
        root = self.source()
        previous = {i.findtext('g:id', namespaces=NS).split('_')[-1]: {
            'product_id':i.findtext('g:item_group_id', namespaces=NS),
            'strategy':'product_first_image','source_url':'https://cdn.shopify.com/original.jpg'
        } for i in root.findall('.//item')}
        error = urllib.error.HTTPError('https://checkout.almighty.tools', 429, 'Too Many Requests', {}, None)
        with patch('build_axon_feed.urllib.request.urlopen', side_effect=error) as request, patch('build_axon_feed.time.sleep'):
            self.assertEqual(shopify_images(ET.tostring(root), previous), previous)
            self.assertEqual(request.call_count, 2)
        with patch('build_axon_feed.urllib.request.urlopen', side_effect=error), patch('build_axon_feed.time.sleep'):
            with self.assertRaises(AssertionError): shopify_images(ET.tostring(root), {})

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

    def test_country_independent_and_legacy_ids_produce_identical_axon_rows(self):
        current = self.source()
        legacy = self.source()
        for root, prefix in [(current, 'Shopify'), (legacy, 'shopify_US')]:
            for item in root.findall('.//item'):
                pid = item.findtext('g:item_group_id', namespaces=NS)
                vid = item.findtext('g:id', namespaces=NS).split('_')[-1]
                item.find('g:id', NS).text = f'{prefix}_{pid}_{vid}'
        self.assertEqual(self.build(current), self.build(legacy))
        previous = {i.findtext('g:id', namespaces=NS).split('_')[-1]: {
            'product_id': i.findtext('g:item_group_id', namespaces=NS),
            'strategy': 'product_first_image', 'source_url': 'https://cdn.shopify.com/original.jpg'
        } for i in current.findall('.//item')}
        error = urllib.error.HTTPError('https://checkout.almighty.tools', 429, 'Too Many Requests', {}, None)
        with patch('build_axon_feed.urllib.request.urlopen', side_effect=error), patch('build_axon_feed.time.sleep'):
            self.assertEqual(shopify_images(ET.tostring(current), previous), shopify_images(ET.tostring(legacy), previous))

    def test_non_us_legacy_or_malformed_id_rejected(self):
        for invalid in ['shopify_GB_1_2', 'Shopify_1_2_extra', 'Shopify_1', '1_2']:
            root = self.source()
            root.find('.//item/g:id', NS).text = invalid
            with self.assertRaises(AssertionError): self.build(root)
            with self.assertRaises(AssertionError): shopify_images(ET.tostring(root))

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
