import unittest

from _ljp.mb.target.product import Get_Product


class PageStub:
    def __init__(self, url):
        self.url = url


class TargetProductTests(unittest.TestCase):
    def setUp(self):
        # These helpers do not require browser or Step4 initialization.
        self.step = Get_Product.__new__(Get_Product)

    @staticmethod
    def _valid_simple_row():
        return {
            "Type": "simple",
            "SKU": "12345678",
            "Name": "Validated product",
            "Description": "<p>Product description</p>",
            "Sale price": "12.99",
            "Regular price": "12.99",
            "Images": "https://target.scene7.com/is/image/Target/GUEST_test",
            "Parent": "",
            "brand": "Target Brand",
            "Stock": 0,
        }

    def test_active_tcin_prefers_preselect_over_path_tcin(self):
        page = PageStub(
            "https://www.target.com/p/product/-/A-100?preselect=200"
        )

        self.assertEqual(self.step._get_current_tcin_from_url(page), "200")

    def test_active_tcin_reads_direct_target_url(self):
        page = PageStub("https://www.target.com/p/product/-/A-100")

        self.assertEqual(self.step._get_current_tcin_from_url(page), "100")

    def test_wait_for_variant_price_returns_immediately_for_selected_variant(self):
        page = PageStub("https://www.target.com/p/product/-/A-100")
        self.step.variant_wait_seconds = 1
        self.step._get_variant_chip_values = lambda _page: [
            {
                "name": "Size",
                "text": "Large",
                "selected": True,
            }
        ]
        self.step._extract_price_from_dom = lambda _page, retry: "9.99"

        price = self.step._wait_for_variant_price(page, [("Size", "Large")])

        self.assertEqual(price, "9.99")

    def test_out_of_stock_variant_still_requires_a_price(self):
        variations = {"100": {"Size": "Small"}, "200": {"Size": "Large"}}
        data = {
            "100": {"price": "8.99"},
            "200": {"price": "", "stock": 0},
        }

        with self.assertRaisesRegex(ValueError, "200"):
            self.step._validate_variant_data(variations, data)

    def test_simple_product_requires_every_cache_field(self):
        valid_row = self._valid_simple_row()
        self.step._validate_rows_before_cache([valid_row])
        self.assertEqual(valid_row["Stock"], 1000)

        invalid_fields = {
            "Sale price": "0",
            "Regular price": "",
        }
        for field, value in invalid_fields.items():
            with self.subTest(field=field):
                row = self._valid_simple_row()
                row[field] = value
                with self.assertRaises(ValueError):
                    self.step._validate_rows_before_cache([row])

    def test_variable_parent_does_not_require_prices(self):
        row = self._valid_simple_row()
        row.update({"Type": "variable"})
        row.pop("Sale price")
        row.pop("Regular price")

        self.step._validate_rows_before_cache([row])

    def test_variation_requires_parent_and_complete_attribute(self):
        row = self._valid_simple_row()
        row.update(
            {
                "Type": "variation",
                "Parent": "12345678",
                "Attribute 1 name": "Size",
                "Attribute 1 value(s)": "Large",
            }
        )
        self.step._validate_rows_before_cache([row])

        row["Attribute 1 value(s)"] = ""
        with self.assertRaisesRegex(ValueError, "属性不完整"):
            self.step._validate_rows_before_cache([row])

    def test_target_cache_gate_reuses_common_simple_requirements(self):
        invalid_row = self._valid_simple_row()
        invalid_row["Images"] = ""

        with self.assertRaisesRegex(ValueError, "simple.*Images"):
            self.step._validate_rows_before_cache([invalid_row])


if __name__ == "__main__":
    unittest.main()
