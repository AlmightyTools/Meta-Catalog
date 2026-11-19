import subprocess
import unittest
from apply_gmc_image_overrides import ROOT, POLICY, normalize, strip_images


class ImageCorrectionTests(unittest.TestCase):
    def test_all_live_feeds_only_images_change(self):
        count = 0
        paths = sorted(ROOT.glob('almighty-tools-gmc-*.xml'))
        self.assertEqual(len(paths), 42)
        for path in paths:
            baseline = subprocess.check_output(['git', 'show', '6d098bb1ecd3c27dec3b09e3e01fe39cbd952ab8:' + path.name], cwd=ROOT)
            result, mapped = normalize(baseline)
            self.assertEqual(mapped, 17, path.name)
            self.assertEqual(strip_images(baseline.decode()), strip_images(result.decode()))
            self.assertEqual(result, path.read_bytes(), path.name)
            self.assertEqual(normalize(result)[0], result)
            count += mapped
        self.assertEqual(count, 714)

    def test_future_source_refresh_and_mismatch(self):
        data = (ROOT / 'almighty-tools-gmc-us.xml').read_bytes()
        current_image = POLICY['50440808530216']['filename'].encode()
        source = data.replace(current_image, b'old-promotional-photo.png')
        self.assertNotEqual(source, data)
        self.assertEqual(normalize(source)[0], data)
        broken = source.replace(b'Shopify_9720607146280_50440808530216', b'Shopify_999_50440808530216')
        with self.assertRaises(ValueError):
            normalize(broken)


if __name__ == '__main__':
    unittest.main()
