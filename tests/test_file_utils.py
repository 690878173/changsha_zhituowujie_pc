import asyncio
import unittest

import pandas as pd

from _ljp.file_utils import WebPValidator


class _ResponseContent:
    async def read(self, size):
        return b"RIFF\x00\x00\x00\x00WEBPVP8 "


class _Response:
    status = 206
    content = _ResponseContent()


class _RequestContext:
    def __init__(self, *, response=None, error=None):
        self.response = response
        self.error = error

    async def __aenter__(self):
        if self.error is not None:
            raise self.error
        return self.response

    async def __aexit__(self, exc_type, exc, traceback):
        return False


class _TimeoutThenWebPSession:
    def __init__(self):
        self.calls = 0

    def get(self, url, *, timeout, headers):
        self.calls += 1
        if self.calls == 1:
            return _RequestContext(error=asyncio.TimeoutError())
        return _RequestContext(response=_Response())


class _AlwaysTimeoutSession:
    def __init__(self):
        self.calls = 0

    def get(self, url, *, timeout, headers):
        self.calls += 1
        return _RequestContext(error=asyncio.TimeoutError())


class WebPValidatorTests(unittest.IsolatedAsyncioTestCase):
    async def test_retries_a_timeout_and_accepts_the_recovered_webp(self):
        session = _TimeoutThenWebPSession()

        valid, message = await WebPValidator._verify_single_url(
            session, "https://example.com/image.webp", timeout=1,
        )

        self.assertTrue(valid)
        self.assertEqual(message, "OK")
        self.assertEqual(session.calls, 2)

    async def test_reports_timeout_after_all_configured_retries(self):
        session = _AlwaysTimeoutSession()

        valid, message = await WebPValidator._verify_single_url(
            session, "https://example.com/image.webp", timeout=1, timeout_retries=2,
        )

        self.assertFalse(valid)
        self.assertEqual(message, "超时")
        self.assertEqual(session.calls, 3)

    def test_rejects_negative_timeout_retries(self):
        with self.assertRaisesRegex(ValueError, "timeout_retries"):
            WebPValidator(df=pd.DataFrame(), timeout_retries=-1)


if __name__ == "__main__":
    unittest.main()
