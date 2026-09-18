"""Playwright implementation for :mod:`_ljp.browser.browser`."""

from __future__ import annotations

import time
from collections.abc import Mapping
from itertools import cycle
from typing import Any

from .browser import BrowserBackend, BrowserConfig, BrowserFetchResponse


FETCH_SCRIPT = """async ({url, options = {}, timeout = null}) => {
    options = options || {};
    const controller = new AbortController();
    let timer = null;
    if (timeout !== null) {
        timer = setTimeout(() => controller.abort(), timeout);
    }
    try {
        const requestOptions = {
            ...options,
            credentials: options.credentials ?? 'include',
            signal: controller.signal,
        };
        if (requestOptions.bodyBytes !== undefined) {
            requestOptions.body = new Uint8Array(requestOptions.bodyBytes);
            delete requestOptions.bodyBytes;
        }
        const response = await fetch(url, requestOptions);
        const headers = {};
        response.headers.forEach((value, key) => { headers[key] = value; });
        const content = Array.from(new Uint8Array(await response.arrayBuffer()));
        let cookies = '';
        try {
            cookies = document.cookie;
        } catch {}
        return {url: response.url, status: response.status, headers, content, cookies};
    } catch (error) {
        return {error: String(error), url, status: 0, headers: {}, content: []};
    } finally {
        if (timer !== null) clearTimeout(timer);
    }
}"""


class PlaywrightBackend(BrowserBackend):
    """Synchronous Playwright backend with per-context fingerprint injection."""

    name = 'playwright'

    @staticmethod
    def _close_contexts(items: list[tuple[Any, Any | None]]) -> None:
        for context, _ in items:
            try:
                context.close()
            except Exception:
                pass

    @staticmethod
    def _blocked_resource_types(config: BrowserConfig) -> set[str]:
        blocked = set(config.block_resource_types)
        if config.block_images:
            blocked.add('image')
        return blocked

    @classmethod
    def _configure_context(cls, context: Any, config: BrowserConfig) -> None:
        if config.extra_http_headers:
            context.set_extra_http_headers(config.extra_http_headers)
        for script in config.init_scripts:
            context.add_init_script(script=script)
        blocked_types = cls._blocked_resource_types(config)
        if blocked_types:
            def route_handler(route: Any) -> None:
                if route.request.resource_type.lower() in blocked_types:
                    route.abort()
                else:
                    route.continue_()

            context.route('**/*', route_handler)

    @staticmethod
    def _fingerprint(config: BrowserConfig) -> Any | None:
        if not config.fingerprint_enabled:
            return None
        try:
            from fingerprint_toolkit import FingerprintKit
        except ImportError as exc:
            raise RuntimeError(
                'Playwright fingerprint mode requires fingerprint_toolkit; set '
                'browser={"fingerprint_enabled": False} to disable it.'
            ) from exc
        return FingerprintKit(**config.fingerprint_options)

    def _create_contexts(self, browser: Any, config: BrowserConfig) -> list[tuple[Any, Any | None]]:
        context_options = dict(config.context_options)
        if config.user_agent and 'user_agent' not in context_options:
            context_options['user_agent'] = config.user_agent
        contexts: list[tuple[Any, Any | None]] = []
        try:
            for _ in range(config.context_count):
                context = browser.new_context(**context_options)
                try:
                    self._configure_context(context, config)
                    fingerprint = self._fingerprint(config)
                except Exception:
                    context.close()
                    raise
                contexts.append((context, fingerprint))
                if config.context_create_delay_ms:
                    time.sleep(config.context_create_delay_ms / 1000)
            return contexts
        except Exception:
            self._close_contexts(contexts)
            raise

    def create_state(self, config: BrowserConfig) -> dict[str, Any]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError('Playwright backend requires playwright.') from exc

        playwright = sync_playwright().start()
        browser = None
        try:
            browser = playwright.chromium.launch(headless=config.headless, **config.launch_options)
            items = self._create_contexts(browser, config)
        except Exception:
            if browser is not None:
                browser.close()
            playwright.stop()
            raise
        return {
            'playwright': playwright,
            'browser': browser,
            'items': items,
            'contexts': cycle(items),
        }

    def get_page(self, state: dict[str, Any], url: str | None, **options: Any) -> Any:
        config: BrowserConfig = options.pop('config')
        wait_for_selector = options.pop('wait_for_selector', None)
        wait_until = options.pop('wait_until', None)
        timeout = options.pop('timeout', None)
        stable_wait_ms = options.pop('stable_wait_ms', None)
        network_idle_timeout = options.pop('network_idle_timeout', None)

        context, fingerprint = next(state['contexts'])
        page = context.new_page()
        if fingerprint is not None:
            fingerprint.inject(page)
        if url is None:
            return page

        navigation_timeout = config.timeout if timeout is None else timeout
        page.goto(
            url,
            wait_until=config.wait_until if wait_until is None else wait_until,
            timeout=navigation_timeout,
            **options,
        )
        if wait_for_selector:
            page.wait_for_selector(wait_for_selector, timeout=navigation_timeout)
        try:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            page.wait_for_load_state(
                'networkidle',
                timeout=config.network_idle_timeout if network_idle_timeout is None else network_idle_timeout,
            )
        except PlaywrightTimeoutError:
            pass
        delay = config.stable_wait_ms if stable_wait_ms is None else stable_wait_ms
        if delay > 0:
            page.wait_for_timeout(delay)
        return page

    @staticmethod
    def _fetch_options(options: Mapping[str, Any]) -> dict[str, Any]:
        result = dict(options)
        body_bytes = result.pop('body_bytes', result.get('bodyBytes', None))
        if body_bytes is not None:
            if not isinstance(body_bytes, (bytes, bytearray, list, tuple)):
                raise TypeError('fetch body_bytes must be bytes or a sequence of byte values.')
            result['bodyBytes'] = list(body_bytes)
        return result

    def fetch(self, state: dict[str, Any], url: str, **options: Any) -> BrowserFetchResponse:
        config: BrowserConfig = state['config']
        page = options.get('page') or self.get_page(state, None, config=config)
        timeout = config.timeout if options.get('timeout') is None else options['timeout']
        payload = page.evaluate(
            FETCH_SCRIPT,
            {
                'url': url,
                'options': self._fetch_options(options.get('options') or {}),
                'timeout': timeout,
            },
        )
        return BrowserFetchResponse.from_payload(payload)

    def expect_response(self, state: dict[str, Any], **options: Any) -> Any:
        timeout = state['config'].timeout if options.get('timeout') is None else options['timeout']
        return options['page'].expect_response(options['url_or_predicate'], timeout=timeout)

    def response_data(self, response: Any) -> BrowserFetchResponse:
        try:
            headers = response.all_headers()
        except AttributeError:
            headers = response.headers
        return BrowserFetchResponse(
            url=response.url,
            status=response.status,
            headers=dict(headers),
            content=response.body(),
        )

    def restart_context(self, state: dict[str, Any], *, relaunch_browser: bool) -> bool:
        if relaunch_browser:
            self.close(state)
            return False
        self._close_contexts(state['items'])
        items = self._create_contexts(state['browser'], state['config'])
        state['items'] = items
        state['contexts'] = cycle(items)
        return True

    def close(self, state: dict[str, Any]) -> None:
        try:
            state['browser'].close()
        finally:
            state['playwright'].stop()
