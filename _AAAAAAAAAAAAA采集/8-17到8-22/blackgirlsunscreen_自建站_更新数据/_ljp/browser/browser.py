"""Thread-local browser facade and backend-independent configuration."""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
from typing import Any, ClassVar


class BrowserConfig:
    """Configuration shared by the Playwright and DrissionPage backends.

    The browser is headed by default. Backend-specific values remain in
    ``launch_options``, ``context_options``, and ``drission_options``.
    """

    _BACKEND_ALIASES = {
        'playwright': 'playwright', 'pw': 'playwright',
        'drissionpage': 'drissionpage', 'drission': 'drissionpage', 'dp': 'drissionpage',
    }

    def __init__(self, options: Mapping[str, Any] | None = None):
        if options is not None and not isinstance(options, Mapping):
            raise TypeError('browser options must be a mapping.')
        options = dict(options or {})
        requested_backend = (
            options.get('backend') or options.get('engine') or options.get('driver') or 'playwright'
        )
        self.backend = self.normalize_backend(requested_backend)
        self.enabled = options.get('enabled', False)
        self.headless = options.get('headless', False)
        self.context_count = options.get('context_count', 4)
        self.context_options = self._copy_mapping(options.get('context_options'), 'context_options')
        self.launch_options = self._copy_mapping(options.get('launch_options'), 'launch_options')
        self.drission_options = self._copy_mapping(options.get('drission_options'), 'drission_options')
        self.extra_http_headers = self._copy_mapping(
            options.get('extra_http_headers', options.get('headers')), 'extra_http_headers',
        )
        self.user_agent = options.get('user_agent')
        self.block_images = options.get('block_images', False)
        self.block_resource_types = self._string_tuple(
            options.get('block_resource_types', ()), 'block_resource_types', lower=True,
        )
        self.blocked_url_patterns = self._string_tuple(
            options.get('blocked_url_patterns', ()), 'blocked_url_patterns',
        )
        self.init_scripts = self._string_tuple(options.get('init_scripts', ()), 'init_scripts')
        self.fingerprint_enabled = options.get('fingerprint_enabled', True)
        self.fingerprint_options = self._copy_mapping(
            options.get('fingerprint_options'), 'fingerprint_options',
        )
        self.context_create_delay_ms = options.get('context_create_delay_ms', 1000)
        self.wait_until = options.get('wait_until', 'domcontentloaded')
        self.timeout = options.get('timeout', 30000)
        self.network_idle_timeout = options.get('network_idle_timeout', 5000)
        self.stable_wait_ms = options.get('stable_wait_ms', 500)
        self._validate()

    @staticmethod
    def _copy_mapping(value: Any, name: str) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise TypeError(f'browser.{name} must be a mapping.')
        return dict(value)

    @staticmethod
    def _string_tuple(value: Any, name: str, *, lower: bool = False) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, str):
            value = (value,)
        if isinstance(value, (bytes, bytearray)) or not isinstance(value, Sequence):
            raise TypeError(f'browser.{name} must be a string or a sequence of strings.')
        result = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise TypeError(f'browser.{name} must contain non-empty strings.')
            result.append(item.strip().lower() if lower else item)
        return tuple(result)

    @classmethod
    def normalize_backend(cls, backend: Any) -> str:
        if not isinstance(backend, str):
            raise ValueError('browser.backend must be a string.')
        normalized = backend.strip().lower()
        if not normalized:
            raise ValueError('browser.backend cannot be empty.')
        return cls._BACKEND_ALIASES.get(normalized, normalized)

    def _validate(self) -> None:
        for name in ('enabled', 'headless', 'block_images', 'fingerprint_enabled'):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f'browser.{name} must be a boolean.')
        if self.user_agent is not None and (not isinstance(self.user_agent, str) or not self.user_agent.strip()):
            raise TypeError('browser.user_agent must be a non-empty string when provided.')
        if set(self.fingerprint_options) - {'seed', 'profile'}:
            raise ValueError('browser.fingerprint_options supports only seed and profile.')
        for name in ('context_count', 'timeout', 'network_idle_timeout',
                     'stable_wait_ms', 'context_create_delay_ms'):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f'browser.{name} must be numeric.')
            if value < 0 or (name in {'context_count', 'timeout'} and value == 0):
                raise ValueError(f'browser.{name} must be greater than zero.')
        if int(self.context_count) != self.context_count:
            raise ValueError('browser.context_count must be an integer.')
        self.context_count = int(self.context_count)


@dataclass(slots=True)
class BrowserFetchResponse:
    """A response obtained through browser-page JavaScript or interception."""

    url: str
    status: int
    headers: dict[str, str]
    content: bytes
    cookies: str = ''
    error: str | None = None

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 400 and self.error is None

    def text(self, encoding: str = 'utf-8', errors: str = 'replace') -> str:
        return self.content.decode(encoding, errors=errors)

    def json(self) -> Any:
        return json.loads(self.text())

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> 'BrowserFetchResponse':
        return cls(
            url=str(payload.get('url') or ''),
            status=int(payload.get('status') or 0),
            headers=dict(payload.get('headers') or {}),
            content=bytes(payload.get('content') or ()),
            cookies=str(payload.get('cookies') or ''),
            error=str(payload['error']) if payload.get('error') else None,
        )


class BrowserBackend(ABC):
    """Backend contract. ``Browser`` owns each state in its calling thread."""

    name: ClassVar[str]

    @abstractmethod
    def create_state(self, config: BrowserConfig) -> dict[str, Any]:
        """Create resources for the current thread."""

    @abstractmethod
    def get_page(self, state: dict[str, Any], url: str | None, **options: Any) -> Any:
        """Return a native backend page, navigating if ``url`` is supplied."""

    @abstractmethod
    def close(self, state: dict[str, Any]) -> None:
        """Close resources for the current thread."""

    def restart_context(self, state: dict[str, Any], *, relaunch_browser: bool) -> bool:
        self.close(state)
        return False

    def fetch(self, state: dict[str, Any], url: str, **options: Any) -> BrowserFetchResponse:
        raise NotImplementedError(f'{self.name} does not support browser-page fetch.')

    def expect_response(self, state: dict[str, Any], **options: Any) -> Any:
        raise NotImplementedError(f'{self.name} does not support response interception.')

    def response_data(self, response: Any) -> BrowserFetchResponse:
        raise NotImplementedError(f'{self.name} does not support response extraction.')


class Browser:
    """Lazy, thread-local browser facade returning native backend pages."""

    _backend_types: ClassVar[dict[str, type[BrowserBackend]]] = {}

    def __init__(self, options: Mapping[str, Any] | None = None):
        self.config = BrowserConfig(options)
        self._local = threading.local()
        self._backend = self._make_backend(self.config.backend)

    @classmethod
    def register_backend(cls, name: str, backend_type: type[BrowserBackend]) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError('Backend name cannot be empty.')
        if not isinstance(backend_type, type) or not issubclass(backend_type, BrowserBackend):
            raise TypeError('backend_type must subclass BrowserBackend.')
        cls._backend_types[name.strip().lower()] = backend_type

    def _make_backend(self, name: str) -> BrowserBackend:
        backend_type = self._backend_types.get(name)
        if backend_type is None:
            available = ', '.join(sorted(self._backend_types))
            raise ValueError(f'Unregistered browser backend {name!r}; available: {available}.')
        return backend_type()

    def _create_state(self) -> dict[str, Any]:
        if not self.config.enabled:
            raise RuntimeError('Browser automation is disabled; set Tool_config(browser={"enabled": True}).')
        backend_name = BrowserConfig.normalize_backend(self.config.backend)
        if backend_name != self._backend.name:
            self.config.backend = backend_name
            self._backend = self._make_backend(backend_name)
        state = self._backend.create_state(self.config)
        state['config'] = self.config
        self._local.state = state
        return state

    def _state(self) -> dict[str, Any]:
        return getattr(self._local, 'state', None) or self._create_state()

    def get_page(self, url: str | None = None, **options: Any) -> Any:
        return self._backend.get_page(self._state(), url, config=self.config, **options)

    def fetch(self, url: str, *, options: Mapping[str, Any] | None = None,
              timeout: int | float | None = None, page: Any | None = None) -> BrowserFetchResponse:
        """Execute ``window.fetch`` in a Playwright page's browser context."""
        if not isinstance(url, str) or not url.strip():
            raise ValueError('url must be a non-empty string.')
        if options is not None and not isinstance(options, Mapping):
            raise TypeError('options must be a mapping.')
        return self._backend.fetch(
            self._state(), url.strip(), options=dict(options or {}), timeout=timeout, page=page,
        )

    def expect_response(self, page: Any, url_or_predicate: Any, *, timeout: int | float | None = None) -> Any:
        """Return Playwright's response expectation context manager for ``page``."""
        if page is None:
            raise ValueError('page is required to intercept a response.')
        return self._backend.expect_response(
            self._state(), page=page, url_or_predicate=url_or_predicate, timeout=timeout,
        )

    def response_data(self, response: Any) -> BrowserFetchResponse:
        """Read a previously intercepted Playwright response into bytes."""
        return self._backend.response_data(response)

    def restart_context(self, *, relaunch_browser: bool = False) -> None:
        state = self._state()
        try:
            keep_state = self._backend.restart_context(state, relaunch_browser=relaunch_browser)
        except Exception:
            self.close()
            raise
        if not keep_state:
            self._local.state = None

    def close(self) -> None:
        state = getattr(self._local, 'state', None)
        if state is None:
            return
        try:
            self._backend.close(state)
        finally:
            self._local.state = None


from .playwright import PlaywrightBackend
from .drission import DrissionPageBackend

Browser._backend_types = {
    PlaywrightBackend.name: PlaywrightBackend,
    DrissionPageBackend.name: DrissionPageBackend,
}

__all__ = [
    'Browser', 'BrowserBackend', 'BrowserConfig', 'BrowserFetchResponse',
    'DrissionPageBackend', 'PlaywrightBackend',
]
