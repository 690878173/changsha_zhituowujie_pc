import unittest
from unittest.mock import patch

from _ljp.mb.target import detail


class FakeResponse:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


class FakeSession:
    responses = []

    def __init__(self, impersonate):
        self.impersonate = impersonate

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def get(self, *args, **kwargs):
        return self.responses.pop(0)


def product_page(path):
    return {
        "data_source_modules": [
            {
                "module_data": {
                    "search_response": {
                        "products": [
                            {
                                "enrichment": {"buy_url": path},
                                "item": {
                                    "product_description": {"title": path}
                                },
                            }
                        ]
                    }
                }
            }
        ]
    }


class TargetDetailTests(unittest.TestCase):
    def test_failed_slp_page_is_retried_after_first_pass(self):
        FakeSession.responses = [
            FakeResponse(500, text="server error"),
            FakeResponse(200, product_page("/p/second")),
            FakeResponse(200, product_page("/p/first")),
        ]

        with (
            patch.object(detail.cffi_requests, "Session", FakeSession),
            patch.object(detail.time, "sleep"),
            patch.object(detail.random, "uniform", return_value=0),
        ):
            result = detail.get_target_detail_urls("test", max_pages=2)

        self.assertEqual(
            result,
            ["https://www.target.com/p/second", "https://www.target.com/p/first"],
        )
        self.assertEqual(FakeSession.responses, [])


if __name__ == "__main__":
    unittest.main()
