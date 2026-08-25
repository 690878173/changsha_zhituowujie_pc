"""Thread-safe HTTP client backed by curl_cffi with bounded retries."""

from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable

import curl_cffi

from .config import _IMPERSONATE_TARGET, Tool_config


@dataclass(slots=True)
class FailedResponse:
    """Response-shaped result returned when every transport attempt fails."""

    url: str
    error: Exception | None = None
    status_code: int = 0
    text: str = ''
    content: bytes = b''
    headers: dict[str, str] | None = None

    @property
    def ok(self) -> bool:
        return False

    def json(self) -> Any:
        raise RuntimeError(f'Request did not produce a response: {self.error}')


class Session:
    """Synchronous HTTP client with one curl session per calling thread."""

    def __init__(self, config: Tool_config, *, session_factory=None,
                 sleep: Callable[[float], None] = time.sleep,
                 random_uniform: Callable[[float, float], float] = random.uniform):
        self.config = config
        self._session_factory = session_factory or self._new_curl_session
        self._sleep = sleep
        self._random_uniform = random_uniform
        self._local = threading.local()
        self._sessions = []
        self._sessions_lock = threading.Lock()

    @staticmethod
    def _new_curl_session():
        return curl_cffi.requests.Session(impersonate=_IMPERSONATE_TARGET)

    @property
    def _session(self):
        session = getattr(self._local, 'session', None)
        if session is None:
            session = self._session_factory()
            self._local.session = session
            with self._sessions_lock:
                self._sessions.append(session)
        return session

    def get(self, url, headers=None, cookies=None, params=None, **kwargs):
        return self.fetch('GET', url, headers=headers, cookies=cookies, params=params, **kwargs)

    def post(self, url, **kwargs):
        return self.fetch('POST', url, **kwargs)

    def fetch(self, method, url, headers=None, cookies=None, params=None, **kwargs):
        """Request a URL and retry transient HTTP statuses or transport errors."""
        request_headers = self.config.headers if headers is None else headers
        request_cookies = self.config.cookies if cookies is None else cookies
        response = None
        last_error = None
        timeout = kwargs.pop('timeout', self.config.time_out)

        for attempt in range(1, self.config.max_retry + 1):
            try:
                response = self._session.request(
                    method,
                    url,
                    headers=request_headers,
                    cookies=request_cookies,
                    timeout=timeout,
                    params=params,
                    **kwargs,
                )
                if response.status_code == 404:
                    r_str = f'页面不存在:{url},返回404,'
                    if params:
                        r_str += f'参数:{params}'
                    print(r_str)
                    return response
                if response.status_code not in self.config.retry_statuses:
                    return response
                if attempt < self.config.max_retry:
                    self._wait_before_retry(attempt, url, f'HTTP {response.status_code}')
            except Exception as exc:
                last_error = exc
                if attempt < self.config.max_retry:
                    self._wait_before_retry(attempt, url, str(exc))

        return response if response is not None else FailedResponse(url=url, error=last_error)

    def _wait_before_retry(self, attempt: int, url: str, reason: str) -> None:
        policy = self.config.retry_backoff
        wait = min(
            policy['base_seconds'] * (2 ** (attempt)),
            policy['max_seconds'],
        )
        if policy['jitter_seconds']:
            wait += self._random_uniform(0.2, policy['jitter_seconds'])
        print(f'[重试] 第{attempt}次重试，等待 {wait:.1f}s: {url} ({reason})')
        self._sleep(wait)

    def close(self):
        """Close every thread-owned curl session created by this client."""
        with self._sessions_lock:
            sessions, self._sessions = self._sessions, []
        for session in sessions:
            try:
                session.close()
            except Exception:
                pass
        self._local.session = None


class Asession:
    """Compatibility wrapper for the legacy ljp_page asynchronous client."""

    def __init__(self, config: Tool_config):
        self.config = config
        from ljp_page.request.session import AsyncSession, CurlCffiAdapter

        self.session = AsyncSession(adapter=CurlCffiAdapter())
        self.session.update_cookies(config.cookies)
        self.session.update_headers(config.headers)
        self.session.config.retry.max_retries = config.max_retry

    async def get(self, url, headers=None, cookies=None, params=None, **kwargs):
        return await self.session.get(
            url,
            headers=self.config.headers if headers is None else headers,
            cookies=self.config.cookies if cookies is None else cookies,
            params=params,
            **kwargs,
        )

    async def close(self):
        await self.session.close()


__all__ = ['Asession', 'FailedResponse', 'Session']
