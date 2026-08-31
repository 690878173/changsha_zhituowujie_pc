"""URL 处理工具"""

from urllib.parse import urljoin, urlsplit, urlunsplit


class URL:

    def __init__(self, config):
        self.config = config
        self.base_url = config.base_url

    def add_site(self, url) -> str:
        if not isinstance(url, str):
            raise TypeError('url must be a string.')
        return urljoin(self.base_url, url)

    @staticmethod
    def site_add(base, url) -> str:
        if not isinstance(base, str) or not isinstance(url, str):
            raise TypeError('base and url must be strings.')
        return urljoin(base, url)

    @staticmethod
    def get_base_domain(url):
        if not isinstance(url, str):
            raise TypeError('url must be a string.')
        if not url.startswith(('http://', 'https://', '//')):
            url = '//' + url  # 补充协议占位符
        parsed = urlsplit(url)
        # 如果 scheme 为空，默认补上 https
        scheme = parsed.scheme if parsed.scheme else 'https'
        return f"{scheme}://{parsed.netloc}"

    @staticmethod
    def get_domain(url):
        if not isinstance(url, str):
            raise TypeError('url must be a string.')
        return urlsplit(url if '://' in url or url.startswith('//') else f'//{url}').netloc

    @staticmethod
    def get_handle(url: str) -> str:
        if not isinstance(url, str):
            raise TypeError('url must be a string.')
        return urlsplit(url).path.rstrip('/').split('/')[-1]

    @staticmethod
    def is_no_url(url, no_url_ls):
        return url in no_url_ls

    @staticmethod
    def check_text_in_url(url, target):
        return target not in url

    @staticmethod
    def del_par(url):
        if not isinstance(url, str):
            raise TypeError('url must be a string.')
        parsed = urlsplit(url)
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, '', parsed.fragment))

    def del_par_and_add_site(self, url):
        return self.add_site(self.del_par(url))

    @staticmethod
    def get_params_str(params):
        sl = '?'
        for k, v in params.items():
            sl += f'{k}={v}&'


        return sl[:-1]
