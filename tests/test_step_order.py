import copy
import time
import unittest

import pandas as pd

from _ljp.mb.base.step_get_detail import GetDetail
from _ljp.mb.base.step_get_product import Get_Product
from _ljp.mb.model import PageModel


class MemoryFile:
    def __init__(self, data=None):
        self.data = copy.deepcopy(data or {})
        self.csv_data = {}

    def load_json(self, path, default=None, strict=False):
        if path not in self.data:
            return copy.deepcopy({} if default is None else default)
        return copy.deepcopy(self.data[path])

    def save_json(self, data, path):
        self.data[path] = copy.deepcopy(data)
        return path

    def save_csv(self, data, path, columns=None):
        self.csv_data[path] = copy.deepcopy(list(data))
        return path

    def read_csv(self, data=None, path=None):
        return pd.DataFrame(data if data is not None else self.csv_data[path])


class MemoryBrowser:
    def close(self):
        pass


class MemoryTool:
    def __init__(self, data=None):
        self.File = MemoryFile(data)
        self.browser = MemoryBrowser()

    def print(self, *args, **kwargs):
        pass

    @staticmethod
    def json_del_url(rows):
        return [{key: value for key, value in row.items() if key != "url"} for row in rows]


class DetailOrderStep(GetDetail):
    def fetch_page(self, page, params):
        return ["product-a", "product-b", "product-a", "product-c"], None


class GiftCardDetailStep(GetDetail):
    def fetch_page(self, page, params):
        return ["product-a", "gift-card", "product-b", "gift_card"], None


class EmptyDetailStep(GetDetail):
    def fetch_page(self, page, params):
        page.set_end()
        return [], None


class ProductOrderStep(Get_Product):
    delays = {"slow": 0.06, "fast": 0.01, "middle": 0.03}

    def __init__(self, *args, **kwargs):
        self.fetch_calls = []
        super().__init__(*args, **kwargs)

    def fetch_product(self, url, category):
        self.fetch_calls.append(url)
        time.sleep(self.delays[url])
        if url == "middle":
            return [
                {
                    "SKU": "middle-parent",
                    "Name": "middle-parent",
                    "Description": "middle parent description",
                    "Images": "https://example.com/middle-parent.jpg",
                    "Sale price": "12.50",
                    "Regular price": "12.50",
                    "Type": "variable",
                },
                {
                    "SKU": "middle-child",
                    "Name": "middle-child",
                    "Description": "middle child description",
                    "Images": "https://example.com/middle-child.jpg",
                    "Sale price": "12.50",
                    "Regular price": "12.50",
                    "Type": "variation",
                    "Parent": "middle-parent",
                },
            ]
        return [{
            "SKU": url,
            "Name": url,
            "Description": f"{url} description",
            "Images": f"https://example.com/{url}.jpg",
            "Sale price": "12.50",
            "Regular price": "12.50",
        }]


class FlakyDetailStep(GetDetail):
    def __init__(self, *args, **kwargs):
        self.calls = 0
        super().__init__(*args, **kwargs)

    def fetch_page(self, page, params):
        self.calls += 1
        if self.calls == 1:
            page.set_fail()
            return [], None
        return ["recovered-product"], None


class FlakyProductStep(Get_Product):
    def __init__(self, *args, **kwargs):
        self.calls = 0
        super().__init__(*args, **kwargs)

    def fetch_product(self, url, category):
        self.calls += 1
        if self.calls == 1:
            return []
        return [{
            "SKU": url,
            "Name": url,
            "Description": "recovered description",
            "Images": "https://example.com/recovered.jpg",
            "Sale price": "12.50",
            "Regular price": "12.50",
        }]


class MissingFieldProductStep(Get_Product):
    def fetch_product(self, url, category):
        return [{
            "SKU": url,
            "Name": "Missing image",
            "Description": "This row must fail before cache insertion.",
            "Images": "",
            "Sale price": "12.50",
            "Regular price": "12.50",
        }]


class InvalidPriceProductStep(Get_Product):
    def fetch_product(self, url, category):
        return [{
            "SKU": url,
            "Name": "Invalid price",
            "Description": "This row must fail before cache insertion.",
            "Images": "not-a-url",
            "Sale price": "0",
            "Regular price": "12.50",
        }]


class StepOrderTests(unittest.TestCase):
    def test_detail_page_dedup_keeps_first_seen_order(self):
        tool = MemoryTool({"input": {"Category": ["collection"]}})
        step = DetailOrderStep(
            tool=tool,
            input_path="input",
            output_path="detail-output",
            catch_path="detail-catch",
            index_path="detail-index",
        )

        step.get_detail_url(PageModel(url="collection", next_url="collection", page=1))

        cached_page = next(iter(step.index.data.values()))
        self.assertEqual(
            next(iter(cached_page.values()))["data"],
            ["product-a", "product-b", "product-c"],
        )

    def test_detail_page_excludes_only_configured_internal_urls(self):
        tool = MemoryTool({"input": {"Category": ["collection"]}})
        step = GiftCardDetailStep(
            tool=tool,
            input_path="input",
            output_path="detail-output",
            catch_path="detail-catch",
            index_path="detail-index",
        )

        step.get_detail_url(PageModel(url="collection", next_url="collection", page=1))

        cached_page = next(iter(step.index.data.values()))
        self.assertEqual(next(iter(cached_page.values()))["data"], ["product-a", "product-b"])

    def test_detail_summary_filters_internal_urls_from_existing_cache(self):
        tool = MemoryTool({"input": {"Category": ["collection"]}})
        step = DetailOrderStep(
            tool=tool,
            input_path="input",
            output_path="detail-output",
            catch_path="detail-catch",
            index_path="detail-index",
        )
        step.index.append(
            "cached-page",
            "collection",
            {"data": ["product-a", "gift-card", "product-b"], "next_url": None, "end": True},
        )
        step.catch.append("Category", "cached-page", "collection")

        self.assertEqual(step.output_res(), {"Category": ["product-a", "product-b"]})

    def test_zero_detail_summary_is_red(self):
        tool = MemoryTool({"input": {"Empty": ["collection"]}})
        printed = []
        tool.print = lambda message, **kwargs: printed.append((message, kwargs.get("color")))
        step = EmptyDetailStep(
            tool=tool,
            input_path="input",
            output_path="detail-output",
            catch_path="detail-catch",
            index_path="detail-index",
        )

        step.run()

        self.assertIn(("  分类「Empty」：汇总到 0 条商品链接。", "red"), printed)
        self.assertTrue(any("汇总详情 URL 总数：0" in message and color == "red" for message, color in printed))

    def test_product_output_keeps_current_task_order_for_new_and_cached_tasks(self):
        input_data = {"First": ["slow", "fast"], "Second": ["middle"]}
        tool = MemoryTool({"input": input_data})
        settings = {
            "tool": tool,
            "input_path": "input",
            "output_path": "result",
            "fail_file": "failures",
            "catch_path": "product-catch",
            "index_path": "product-index",
            "output_ts_file": "test-result",
            "max_threads": 3,
        }

        first_run = ProductOrderStep(**settings)
        first_rows = first_run.run()
        self.assertEqual(
            [row["Name"] for row in first_rows],
            ["slow", "fast", "middle-parent", "middle-child"],
        )

        tool.File.data["input"] = {"Second": ["middle"], "First": ["fast", "slow"]}
        cached_run = ProductOrderStep(**settings)
        cached_rows = cached_run.run()

        self.assertEqual(cached_run.fetch_calls, [])
        self.assertEqual(
            [row["Name"] for row in cached_rows],
            ["middle-parent", "middle-child", "fast", "slow"],
        )
        self.assertTrue(all(row["Stock"] == 1000 for row in cached_rows))

    def test_detail_retries_first_pass_failure_after_categories_finish(self):
        tool = MemoryTool({"input": {"Category": ["collection"]}})
        step = FlakyDetailStep(
            tool=tool,
            input_path="input",
            output_path="detail-output",
            catch_path="detail-catch",
            index_path="detail-index",
        )

        result = step.run()

        self.assertEqual(step.calls, 2)
        self.assertEqual(result, {"Category": ["recovered-product"]})
        self.assertFalse(step.failed_pages)

    def test_product_retries_first_pass_failure_and_clears_fail_file(self):
        tool = MemoryTool({"input": {"Category": ["product"]}})
        step = FlakyProductStep(
            tool=tool,
            input_path="input",
            output_path="result",
            fail_file="failures",
            catch_path="product-catch",
            index_path="product-index",
            output_ts_file="test-result",
            max_threads=1,
        )

        rows = step.run()

        self.assertEqual(step.calls, 2)
        self.assertEqual([row["SKU"] for row in rows], ["product"])
        self.assertEqual(tool.File.data["failures"], {})
        self.assertFalse(step.failures)

    def test_missing_common_field_is_not_written_to_product_cache(self):
        tool = MemoryTool({"input": {"Category": ["product"]}})
        step = MissingFieldProductStep(
            tool=tool,
            input_path="input",
            output_path="result",
            fail_file="failures",
            catch_path="product-catch",
            index_path="product-index",
            output_ts_file="test-result",
            max_threads=1,
        )

        rows = step.run()

        self.assertEqual(rows, [])
        self.assertEqual(tool.File.data["product-index"], {})
        self.assertEqual(tool.File.data["failures"], {"Category": ["product"]})

    def test_non_positive_price_is_not_written_to_product_cache(self):
        tool = MemoryTool({"input": {"Category": ["product"]}})
        step = InvalidPriceProductStep(
            tool=tool,
            input_path="input",
            output_path="result",
            fail_file="failures",
            catch_path="product-catch",
            index_path="product-index",
            output_ts_file="test-result",
            max_threads=1,
        )

        rows = step.run()

        self.assertEqual(rows, [])
        self.assertEqual(tool.File.data["product-index"], {})
        self.assertEqual(tool.File.data["failures"], {"Category": ["product"]})

    def test_nonempty_values_do_not_require_url_or_source_validation(self):
        step = Get_Product.__new__(Get_Product)
        row = {
            "SKU": "product",
            "Name": "Product",
            "Description": "<p></p>",
            "Images": "image-reference",
            "Sale price": "12.50",
            "Regular price": "12.50",
        }

        step._validate_rows_before_cache([row])

        self.assertEqual(row["Stock"], 1000)

    def test_cache_requirements_depend_on_product_type(self):
        step = Get_Product.__new__(Get_Product)
        parent = {
            "Type": "variable",
            "SKU": "parent",
            "Name": "Parent",
            "Description": "Parent description",
            "Images": "parent-image",
        }
        variation = {
            "Type": "variation",
            "SKU": "child",
            "Name": "Child",
            "Parent": "parent",
            "Sale price": "12.50",
            "Regular price": "12.50",
        }

        step._validate_rows_before_cache([parent, variation])

        self.assertEqual(parent["Stock"], 1000)
        self.assertEqual(variation["Stock"], 1000)

        invalid_parent = dict(parent, Images="")
        with self.assertRaisesRegex(ValueError, "variable.*Images"):
            step._validate_rows_before_cache([invalid_parent])

        invalid_variation = dict(variation, Parent="")
        with self.assertRaisesRegex(ValueError, "variation.*Parent"):
            step._validate_rows_before_cache([invalid_variation])

        invalid_variation_price = dict(variation, **{"Sale price": "0"})
        with self.assertRaisesRegex(ValueError, "variation.*Sale price"):
            step._validate_rows_before_cache([invalid_variation_price])


if __name__ == "__main__":
    unittest.main()
