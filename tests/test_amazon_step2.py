import copy
import unittest
from unittest.mock import patch

from _ljp.mb.amazon.step2 import YMXStep2


class MemoryFile:
    def __init__(self, data):
        self.data = copy.deepcopy(data)

    def load_json(self, path, default=None, strict=False):
        return copy.deepcopy(self.data.get(path, {} if default is None else default))

    def save_json(self, data, path):
        self.data[path] = copy.deepcopy(data)
        return path

    @staticmethod
    def path_add_site(path):
        return path


class MemoryBrowser:
    def close(self):
        pass


class EmptyVariantResponse:
    status_code = 200
    text = "<html><head><title>Simple product</title></head><body></body></html>"


class MemoryTool:
    def __init__(self, data):
        self.File = MemoryFile(data)
        self.browser = MemoryBrowser()
        self.requests = 0

    def get(self, *args, **kwargs):
        self.requests += 1
        return EmptyVariantResponse()

    def print(self, *args, **kwargs):
        pass


class AmazonStep2Tests(unittest.TestCase):
    def test_empty_variants_keep_source_asin_and_retry_it(self):
        asin = "B000000000"
        tool = MemoryTool({"input": {"Category": [asin]}})
        step = YMXStep2(
            tool=tool,
            input_path="input",
            output_path="output",
            catch_path="catch",
            index_path="index",
        )

        with (
            patch("_ljp.mb.amazon.step2.time.sleep"),
            patch("builtins.print"),
        ):
            result = step.run()

        self.assertEqual(tool.requests, 2)
        self.assertEqual(result, {"Category": [asin]})
        cached_page = next(iter(tool.File.data["index"].values()))
        cached_result = next(iter(cached_page.values()))
        self.assertEqual(cached_result["data"], [asin])
        self.assertTrue(cached_result["fail"])
        self.assertIn("Category", tool.File.data["catch"])
        self.assertEqual(len(step.failed_pages), 1)

        next_run = YMXStep2(
            tool=tool,
            input_path="input",
            output_path="output",
            catch_path="catch",
            index_path="index",
        )
        with (
            patch("_ljp.mb.amazon.step2.time.sleep"),
            patch("builtins.print"),
        ):
            next_run.run()

        self.assertEqual(tool.requests, 4)


if __name__ == "__main__":
    unittest.main()
