"""Small, reusable DrissionPage browser wrapper.

Site Steps should keep their crawl and parsing rules local. This module owns
only browser setup and the common browser operations those Steps need. It is
safe to construct a :class:`Drission` object without starting Chromium; the
process is started on the first operation that needs a page.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from itertools import cycle
import time
from typing import Any


@dataclass(slots=True)
class DrissionConfig:
    """Configuration used to create a ``DrissionPage.ChromiumPage``.

    Timeouts are expressed in milliseconds, matching the project browser
    configuration. ``no_imgs`` prevents image resources from loading and
    ``headless`` adds Chromium's modern headless flag.
    """

    headless: bool = False
    no_imgs: bool = False
    timeout: int | float = 30_000
    browser_path: str | None = None
    address: str | None = None
    local_port: int | None = None
    user_data_path: str | None = None
    cache_path: str | None = None
    download_path: str | None = None
    user_agent: str | None = None
    proxy: str | None = None
    auto_port: bool | None = None
    arguments: Sequence[str] = field(default_factory=tuple)
    preferences: Mapping[str, Any] = field(default_factory=dict)
    headers: Mapping[str, str] = field(default_factory=dict)
    cookies: Mapping[str, str] | Sequence[Mapping[str, Any]] = field(default_factory=dict)
    blocked_urls: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if isinstance(self.timeout, bool) or not isinstance(self.timeout, (int, float)) or self.timeout <= 0:
            raise ValueError('timeout must be a positive number of milliseconds.')
        if self.local_port is not None and (
            isinstance(self.local_port, bool)
            or not isinstance(self.local_port, int)
            or not 1 <= self.local_port <= 65535
        ):
            raise ValueError('local_port must be an integer between 1 and 65535.')
        if self.address and self.local_port is not None:
            raise ValueError('address and local_port cannot be configured together.')
        if isinstance(self.arguments, (str, bytes)) or not isinstance(self.arguments, Sequence):
            raise TypeError('arguments must be a sequence of Chromium argument strings.')
        if not all(isinstance(argument, str) and argument for argument in self.arguments):
            raise TypeError('arguments must contain non-empty strings.')
        if not isinstance(self.preferences, Mapping):
            raise TypeError('preferences must be a mapping.')
        if not isinstance(self.headers, Mapping):
            raise TypeError('headers must be a mapping.')
        if not isinstance(self.cookies, Mapping) and (
            isinstance(self.cookies, (str, bytes)) or not isinstance(self.cookies, Sequence)
        ):
            raise TypeError('cookies must be a mapping or a sequence of cookie mappings.')
        if isinstance(self.blocked_urls, (str, bytes)) or not isinstance(self.blocked_urls, Sequence):
            raise TypeError('blocked_urls must be a sequence of URL patterns.')
        if not all(isinstance(url, str) and url for url in self.blocked_urls):
            raise TypeError('blocked_urls must contain non-empty URL patterns.')

        self.arguments = tuple(self.arguments)
        self.preferences = dict(self.preferences)
        self.headers = dict(self.headers)
        self.cookies = dict(self.cookies) if isinstance(self.cookies, Mapping) else tuple(self.cookies)
        self.blocked_urls = tuple(self.blocked_urls)

    @classmethod
    def from_options(cls, options: Mapping[str, Any] | None = None, **overrides: Any) -> 'DrissionConfig':
        """Build configuration from direct or nested ``drission_options`` data."""
        values = dict(options or {})
        nested = values.pop('drission_options', None)
        allowed = set(cls.__dataclass_fields__)
        if nested is not None:
            if not isinstance(nested, Mapping):
                raise TypeError('drission_options must be a mapping.')
            # A complete Tool_config.browser mapping also has backend-level
            # keys (enabled, backend and context_count). They do not belong to
            # ChromiumOptions; retain only settings this class owns.
            values = {**nested, **{name: value for name, value in values.items() if name in allowed}}
        values.update(overrides)
        unknown = sorted(set(values) - allowed)
        if unknown:
            raise TypeError(f'Unsupported Drission configuration: {", ".join(unknown)}.')
        return cls(**values)

    def build_options(self) -> Any:
        """Create configured native ``ChromiumOptions`` without launching Chrome."""
        try:
            from DrissionPage import ChromiumOptions
        except ImportError as exc:
            raise RuntimeError('Drission requires the DrissionPage package.') from exc

        options = ChromiumOptions()
        if self.browser_path:
            options.set_browser_path(self.browser_path)
        if self.address:
            options.set_address(self.address)
        elif self.local_port is not None:
            options.set_local_port(self.local_port)
        if self.user_data_path:
            options.set_user_data_path(self.user_data_path)
        if self.cache_path:
            options.set_cache_path(self.cache_path)
        if self.download_path:
            options.set_download_path(self.download_path)
        if self.user_agent:
            options.set_user_agent(self.user_agent)
        if self.proxy:
            options.set_proxy(self.proxy)
        if self.no_imgs:
            options.no_imgs(True)

        use_auto_port = self.auto_port
        if use_auto_port is None:
            use_auto_port = not self.address and self.local_port is None
        if use_auto_port:
            options.auto_port()

        has_headless_argument = any(argument.startswith('--headless') for argument in self.arguments)
        for argument in self.arguments:
            options.set_argument(argument)
        if self.headless and not has_headless_argument:
            options.set_argument('--headless=new')
        for name, value in self.preferences.items():
            options.set_pref(name, value)
        return options


class Drission:
    """Thread-local owner of a native DrissionPage browser page.

    The ``page`` property returns the original ``ChromiumPage``. Code that
    needs a DrissionPage-specific capability can use it directly, while common
    operations are available through this wrapper for every crawler Step.
    """

    def __init__(self, options: DrissionConfig | Mapping[str, Any] | None = None, **overrides: Any):
        if isinstance(options, DrissionConfig):
            if overrides:
                raise TypeError('Keyword options cannot be combined with a DrissionConfig instance.')
            self.config = options
        elif options is None or isinstance(options, Mapping):
            self.config = DrissionConfig.from_options(options, **overrides)
        else:
            raise TypeError('options must be DrissionConfig, a mapping, or None.')
        self._pages: dict[int, Any] = {}

    def _page_for_current_thread(self) -> Any:
        import threading

        thread_id = threading.get_ident()
        page = self._pages.get(thread_id)
        if page is not None:
            return page
        try:
            from DrissionPage import ChromiumPage
        except ImportError as exc:
            raise RuntimeError('Drission requires the DrissionPage package.') from exc
        page = ChromiumPage(self.config.build_options(), timeout=self.config.timeout / 1000)
        self._pages[thread_id] = page
        try:
            if self.config.headers:
                page.set.headers(self.config.headers)
            if self.config.cookies:
                page.set.cookies(self.config.cookies)
            if self.config.blocked_urls:
                page.set.blocked_urls(list(self.config.blocked_urls))
        except Exception:
            self.close_current_thread()
            raise
        return page

    @property
    def page(self) -> Any:
        """Return the native ``ChromiumPage`` for the calling thread."""
        return self._page_for_current_thread()

    def get(self, url: str, *, timeout: int | float | None = None,
            retry: int | None = None, interval: int | float | None = None) -> Any:
        """Navigate to ``url`` and return the native page."""
        if not isinstance(url, str) or not url.strip():
            raise ValueError('url must be a non-empty string.')
        timeout_ms = self.config.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'timeout': timeout_ms / 1000}
        if retry is not None:
            kwargs['retry'] = retry
        if interval is not None:
            kwargs['interval'] = interval / 1000
        page = self.page
        page.get(url, **kwargs)
        return page

    open = get
    navigate = get

    @property
    def html(self) -> str:
        """Return current page HTML for parsers such as lxml."""
        return self.page.html

    @property
    def url(self) -> str:
        return self.page.url

    @property
    def title(self) -> str:
        return self.page.title

    def ele(self, locator: Any, *, timeout: int | float | None = None) -> Any:
        """Return one native DrissionPage element."""
        timeout_ms = self.config.timeout if timeout is None else timeout
        return self.page.ele(locator, timeout=timeout_ms / 1000)

    def eles(self, locator: Any, *, timeout: int | float | None = None) -> Any:
        """Return all native DrissionPage elements matching ``locator``."""
        timeout_ms = self.config.timeout if timeout is None else timeout
        return self.page.eles(locator, timeout=timeout_ms / 1000)

    def scroll_to_half(self) -> None:
        self.page.scroll.to_half()

    def scroll_to_bottom(self) -> None:
        self.page.scroll.to_bottom()

    def run_js(self, script: str, *args: Any) -> Any:
        return self.page.run_js(script, *args)

    def set_cookies(self, cookies: Mapping[str, str] | Sequence[Mapping[str, Any]]) -> None:
        self.page.set.cookies(cookies)

    def close_current_thread(self) -> None:
        """Close only the Chromium process owned by the calling thread."""
        import threading

        page = self._pages.pop(threading.get_ident(), None)
        if page is not None:
            try:
                page.quit()
            except Exception:
                pass

    def close(self) -> None:
        """Close all pages created by this wrapper. Safe to call repeatedly."""
        pages, self._pages = tuple(self._pages.values()), {}
        for page in pages:
            try:
                page.quit()
            except Exception:
                pass

    quit = close

    def __enter__(self) -> 'Drission':
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> bool:
        self.close()
        return False


class config(DrissionConfig):
    """Backward-compatible spelling for older imports."""


from .browser import BrowserBackend, BrowserConfig


class DrissionPageBackend(BrowserBackend):
    """DrissionPage backend using the same configuration as :class:`Browser`."""

    name = 'drissionpage'
    _RESOURCE_PATTERNS = {
        'font': ('*.woff', '*.woff2', '*.ttf', '*.otf'),
        'media': ('*.mp3', '*.mp4', '*.avi', '*.mov', '*.webm'),
        'script': ('*.js', '*.js?*'),
        'stylesheet': ('*.css', '*.css?*'),
    }

    @classmethod
    def _make_config(cls, config: BrowserConfig) -> DrissionConfig:
        values = dict(config.drission_options)
        values.setdefault('headless', config.headless)
        values.setdefault('timeout', config.timeout)
        if config.user_agent and not values.get('user_agent'):
            values['user_agent'] = config.user_agent

        headers = dict(config.extra_http_headers)
        headers.update(values.get('headers') or {})
        if headers:
            values['headers'] = headers

        blocked_urls = list(values.get('blocked_urls') or ())
        blocked_urls.extend(config.blocked_url_patterns)
        for resource_type in config.block_resource_types:
            blocked_urls.extend(cls._RESOURCE_PATTERNS.get(resource_type, ()))
        if blocked_urls:
            values['blocked_urls'] = tuple(dict.fromkeys(blocked_urls))

        values['no_imgs'] = bool(
            values.get('no_imgs') or config.block_images or 'image' in config.block_resource_types
        )
        return DrissionConfig.from_options(values)

    @staticmethod
    def _configure_page(page: Any, config: DrissionConfig) -> None:
        if config.headers:
            page.set.headers(config.headers)
        if config.cookies:
            page.set.cookies(config.cookies)
        if config.blocked_urls:
            page.set.blocked_urls(list(config.blocked_urls))

    def create_state(self, config: BrowserConfig) -> dict[str, Any]:
        try:
            from DrissionPage import ChromiumPage
        except ImportError as exc:
            raise RuntimeError('DrissionPage backend requires DrissionPage.') from exc

        drission_config = self._make_config(config)
        page = ChromiumPage(
            drission_config.build_options(), timeout=drission_config.timeout / 1000,
        )
        items = [page]
        try:
            for _ in range(config.context_count - 1):
                items.append(page.new_tab(background=True))
            for item in items:
                self._configure_page(item, drission_config)
        except Exception:
            try:
                page.quit()
            except Exception:
                pass
            raise
        return {
            'page': page,
            'items': items,
            'pages': cycle(items),
            'drission_config': drission_config,
        }

    def get_page(self, state: dict[str, Any], url: str | None, **options: Any) -> Any:
        config: BrowserConfig = options.pop('config')
        wait_for_selector = options.pop('wait_for_selector', None)
        timeout = options.pop('timeout', None)
        stable_wait_ms = options.pop('stable_wait_ms', None)
        options.pop('wait_until', None)
        options.pop('network_idle_timeout', None)
        if options:
            names = ', '.join(sorted(options))
            raise TypeError(f'DrissionPage does not support get_page() options: {names}.')

        page = next(state['pages'])
        if url is None:
            return page
        navigation_timeout = config.timeout if timeout is None else timeout
        page.get(url, timeout=navigation_timeout / 1000)
        if wait_for_selector:
            page.ele(wait_for_selector, timeout=navigation_timeout / 1000)
        delay = config.stable_wait_ms if stable_wait_ms is None else stable_wait_ms
        if delay > 0:
            time.sleep(delay / 1000)
        return page

    def close(self, state: dict[str, Any]) -> None:
        try:
            state['page'].quit()
        except Exception:
            pass


__all__ = ['Drission', 'DrissionConfig', 'DrissionPageBackend', 'config']
