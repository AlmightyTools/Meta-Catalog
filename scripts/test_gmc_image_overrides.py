import unittest
import xml.etree.ElementTree as ET
from apply_gmc_image_overrides import G, ROOT, POLICY, normalize, strip_images


class ImageCorrectionTests(unittest.TestCase):
    def test_all_live_feeds_only_images_change(self):
        paths = sorted(ROOT.glob('almighty-tools-gmc-*.xml'))
        self.assertTrue(paths)
        bundle_matches = 0
        for path in paths:
            baseline = path.read_bytes()
            result, _ = normalize(baseline)
            self.assertEqual(strip_images(baseline.decode()), strip_images(result.decode()))
            self.assertEqual(normalize(result)[0], result)
            for item in ET.fromstring(result).iter('item'):
                identity = item.findtext(G + 'id', '')
                if identity.endswith('_9482682532136_49937880252712'):
                    self.assertTrue(item.findtext(G + 'image_link').endswith(
                        POLICY['49937880252712']['filename']))
                    self.assertIsNone(item.find(G + 'additional_image_link'))
                    bundle_matches += 1
        self.assertGreater(bundle_matches, 0)

    def test_future_source_refresh_and_mismatch(self):
        data, _ = normalize((ROOT / 'almighty-tools-gmc-us.xml').read_bytes())
        current_image = POLICY['49937880252712']['filename'].encode()
        source = data.replace(current_image, b'old-promotional-photo.png')
        self.assertNotEqual(source, data)
        self.assertEqual(normalize(source)[0], data)
        broken = source.replace(b'Shopify_9482682532136_49937880252712',
                                b'Shopify_999_49937880252712')
        self.assertNotEqual(broken, source)
        with self.assertRaises(ValueError):
            normalize(broken)


if __name__ == '__main__':
    unittest.main()
