import unittest

import pandas as pd

from _ljp.mb.base.step_imgs import Replace_imgs


class ReplaceImageOrderTests(unittest.TestCase):
    def test_reverses_product_blocks_without_splitting_variations(self):
        source = pd.DataFrame([
            {"Type": "simple", "SKU": "simple-first", "Parent": ""},
            {"Type": "variable", "SKU": "parent-a", "Parent": ""},
            {"Type": "variation", "SKU": "a-small", "Parent": "parent-a"},
            {"Type": "variation", "SKU": "a-large", "Parent": "parent-a"},
            {"Type": "variable", "SKU": "parent-b", "Parent": ""},
            {"Type": "variation", "SKU": "b-small", "Parent": "parent-b"},
            {"Type": "simple", "SKU": "simple-last", "Parent": ""},
        ])

        result = Replace_imgs.reverse_product_families(source)

        self.assertEqual(
            result["SKU"].tolist(),
            [
                "simple-last",
                "parent-b",
                "b-small",
                "parent-a",
                "a-small",
                "a-large",
                "simple-first",
            ],
        )

    def test_rejects_a_variation_that_is_not_after_its_parent(self):
        source = pd.DataFrame([
            {"Type": "variation", "SKU": "orphan", "Parent": "parent-a"},
        ])

        with self.assertRaisesRegex(ValueError, "未紧跟其父商品"):
            Replace_imgs.reverse_product_families(source)

    def test_keeps_order_when_product_family_columns_are_absent(self):
        source = pd.DataFrame({"Images": ["first.jpg", "second.jpg"]})

        result = Replace_imgs.reverse_product_families(source)

        self.assertEqual(result["Images"].tolist(), ["first.jpg", "second.jpg"])


if __name__ == "__main__":
    unittest.main()
