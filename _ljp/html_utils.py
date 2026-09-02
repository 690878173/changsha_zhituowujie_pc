import json
import re
from pathlib import Path

import pandas as pd
from lxml import etree
from .simtool import SimTool

class HTML:

    TEXT_FIELD_NAMES = frozenset({
        'description',
        'anniu',
        'bubian',
        'body (html)',
        'seo description',
        'short description (product.metafields.c_f.short_description)',
        'zdy-miaoshu (product.metafields.zdy.bianti_miaoshu)',
    })
    TEXT_FIELD_KEYWORDS = (
        'description', 'metafield', 'miaoshu', 'anniu', 'bubian',
        'detail', 'feature', 'dimension', 'warranty', 'specification',
        'use and care',
    )
    TEXT_FIELD_DROP_TAGS = frozenset({
        'script', 'style', 'noscript', 'svg', 'select', 'option', 'button',
        'form', 'iframe', 'template',
    })
    TEXT_FIELD_ALLOW_TAGS = frozenset({
        'p', 'br', 'ul', 'ol', 'li', 'strong', 'b', 'em', 'i',
    })
    _RAW_URL_RE = re.compile(r"https?://[^\s\"'<>]+")
    _EMPTY_TEXT_TAG_RE = re.compile(r'<(p|li|ul|ol|strong|b|em|i)>\s*</\1>', re.I)
    _BR_TAG_RE = re.compile(r'<br\s*/?>', re.I)
    _MULTI_BREAK_RE = re.compile(r'(?:<br>\s*){3,}', re.I)
    _MULTI_SPACE_RE = re.compile(r'[ \t]{2,}')

    def __init__(self, config):
        self.config = config
        self.base_url = config.base_url

    # ── 静态工具方法 ──────────────────────────────────
    @staticmethod
    def extract_js_object(text, var_name='window.menuData'):
        """
        从 JavaScript 代码中提取指定变量赋值的对象（支持嵌套大括号）
        返回解析后的 Python 字典，若失败则返回 None
        """
        # 1. 定位变量赋值位置
        pattern = re.compile(rf'{re.escape(var_name)}\s*=\s*')
        match = pattern.search(text)
        if not match:
            return None

        start = match.end()  # 赋值号之后的位置

        # 2. 从 start 开始查找第一个 '{'
        brace_start = text.find('{', start)
        if brace_start == -1:
            return None

        # 3. 括号计数，找到匹配的 '}'
        count = 0
        for i in range(brace_start, len(text)):
            ch = text[i]
            if ch == '{':
                count += 1
            elif ch == '}':
                count -= 1
                if count == 0:
                    json_str = text[brace_start:i + 1]
                    # 4. 解析为 JSON
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        # 如果包含尾部逗号等非标准语法，回退到 json5
                        try:
                            import json5
                            return json5.loads(json_str)
                        except ImportError:
                            # 如果未安装 json5，可以尝试清理尾部逗号后再试
                            # 这里简单返回 None
                            return None
        return None

    @staticmethod
    def drop_script(html: str) -> str:
        html = html.replace("<script", "<!-- <script")
        html = html.replace("</script>", "</script> -->")
        return html

    @classmethod
    def is_text_field(cls, field_name) -> bool:
        """Return whether a column/metafield should receive rich-text cleaning."""
        if not isinstance(field_name, str):
            return False
        lowered = field_name.strip().lower()
        return lowered in cls.TEXT_FIELD_NAMES or any(
            keyword in lowered for keyword in cls.TEXT_FIELD_KEYWORDS
        )

    @classmethod
    def detect_text_fields(cls, field_names):
        """Return description-like field names in their original input order."""
        return [field_name for field_name in field_names if cls.is_text_field(field_name)]

    @classmethod
    def clean_text_field(cls, value) -> str:
        """String wrapper for the tree-based product-description cleaner."""
        if isinstance(value, etree._Element):
            return cls.clean_product_desc(value)
        if value is None:
            return ''
        try:
            if pd.isna(value):
                return ''
        except (TypeError, ValueError):
            pass
        text = str(value).strip()
        if not text:
            return ''
        return cls.clean_product_desc(etree.HTML(text))

    @classmethod
    def clean_text_fields_df(cls, df, columns=None, *, inplace=False):
        """Clean description fields in a DataFrame and return that DataFrame.

        ``columns=None`` auto-detects fields using the same names and keywords
        as the original cleaner. A list/tuple or comma-separated string selects
        explicit columns instead. Missing requested columns are ignored, as in
        the original row-based implementation. The default returns a copy;
        ``inplace=True`` mutates and returns the supplied DataFrame.
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError('df must be a pandas DataFrame.')
        result = df if inplace else df.copy()
        if columns is None:
            target_columns = cls.detect_text_fields(result.columns)
        elif isinstance(columns, str):
            target_columns = [name.strip() for name in columns.split(',') if name.strip()]
        else:
            try:
                target_columns = list(columns)
            except TypeError as exc:
                raise TypeError('columns must be None, a string, or an iterable of names.') from exc

        for column in target_columns:
            if column in result.columns:
                result[column] = result[column].map(cls.clean_text_field)
        return result

    @staticmethod
    def save(res_text, file_path=None):
        target = file_path or "1.html"
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(HTML.drop_script(res_text))

    @staticmethod
    def save_handle(res_text,handle):
        target = f'html/{handle}'
        if '.html' not in target:
            target +='.html'
        HTML.save(res_text,target)

    @staticmethod
    def save_raw(res_text, file_path=None):
        """Save HTML exactly as received, including executable script tags."""
        target = file_path or "1.html"
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(res_text)

    @staticmethod
    def to_str(node) -> str:
        return etree.tostring(node, encoding="utf-8").decode("utf-8")

    @staticmethod
    def get_text(node) -> str:
        return "".join(node.xpath(".//text()")).strip()

    @staticmethod
    def get_a_text_and_url(a_node) ->tuple[str, str]:
        if isinstance(a_node, list):
            from .simtool import SimTool
            SimTool.print("a标签误传入列表")
            return "", ""
        text = "".join(a_node.xpath(".//text()")).strip()
        url = a_node.get("href", "")
        return text, url

    @staticmethod
    def find_child_a_text_and_url(node):
        return HTML.get_a_text_and_url(node.xpath(".//a")[0])

    @staticmethod
    def del_a_href_to_str(node):
        for a in node.xpath("//a"):
            if "href" in a.attrib:
                del a.attrib["href"]
        return etree.tostring(node, encoding="utf-8").decode("utf-8")

    @staticmethod
    def script_text(html, window_type=r"window\.__INITIAL_STATE__"):
        m = re.search(window_type + r"\s*=\s*(\{.*?\});\s*", html, re.DOTALL)
        return m.group(1) if m else None

    @staticmethod
    def strip_all_attrs(tree):
        for el in tree.iter():
            if isinstance(el.tag, str):
                el.attrib.clear()

    @staticmethod
    def _drop_tag_keep_children(tree, tag):
        pmap = {c: p for p in tree.iter() for c in p}
        for el in tree.xpath(f"//{tag}"):
            parent = pmap.get(el)
            if parent is None:
                continue
            t = el.text or ""
            if t:
                prev = el.getprevious()
                if prev is not None:
                    prev.tail = (prev.tail or "") + t
                else:
                    parent.text = (parent.text or "") + t
            if el.tail:
                children = list(el)
                if children:
                    children[-1].tail = (children[-1].tail or "") + el.tail
                else:
                    prev = el.getprevious()
                    if prev is not None:
                        prev.tail = (prev.tail or "") + el.tail
                    else:
                        parent.text = (parent.text or "") + el.tail
            idx = list(parent).index(el) if el in parent else None
            if idx is not None:
                for child in reversed(list(el)):
                    parent.insert(idx, child)
                parent.remove(el)

    @classmethod
    def clean_product_desc(cls, tree) -> str:
        """Clean an lxml tree using the description-field allow-list policy.

        The method intentionally accepts an already parsed tree so callers can
        keep their existing parser and XPath flow. Block tags and their content
        are removed; other non-whitelisted tags (including ``a``) are unwrapped
        to preserve text and allowed descendants without retaining attributes.
        """
        if isinstance(tree, list):
            SimTool.print("desc误传入列表")
            return ""
        if isinstance(tree, str):
            SimTool.print("desc误传入字符串")
            return ""
        if tree is None or not isinstance(tree, etree._Element):
            return ""

        # Matches the absorbed script policy: discard dangerous block content,
        # then unwrap every remaining tag outside the explicit rich-text list.
        etree.strip_elements(tree, *cls.TEXT_FIELD_DROP_TAGS)
        unsupported_tags = {
            element.tag
            for element in tree.iter()
            if isinstance(element.tag, str)
            and element.tag.lower() not in cls.TEXT_FIELD_ALLOW_TAGS
            and element.tag.lower() not in {'html', 'body'}
        }
        if unsupported_tags:
            etree.strip_tags(tree, *unsupported_tags)
        HTML.strip_all_attrs(tree)
        body = tree.find(".//body")
        root = body if body is not None else tree
        inner = [root.text or '']
        for child in root:
            inner.append(etree.tostring(child, encoding='unicode', method='html', with_tail=False))
            if child.tail:
                inner.append(child.tail)
        return cls._normalize_clean_html(''.join(inner))

    @classmethod
    def _normalize_clean_html(cls, value: str) -> str:
        """Apply the absorbed script's URL, empty-tag and whitespace rules."""
        value = value.replace('\r\n', '\n').replace('\r', '\n')
        value = cls._RAW_URL_RE.sub('', value)
        value = value.replace('&nbsp;', ' ').replace('&#160;', ' ').replace('\xa0', ' ')
        value = cls._BR_TAG_RE.sub('<br>', value)
        value = cls._EMPTY_TEXT_TAG_RE.sub('', value)
        value = cls._MULTI_BREAK_RE.sub('<br><br>', value)
        value = cls._MULTI_SPACE_RE.sub(' ', value)
        value = re.sub(r'>\s+<', '><', value)
        value = re.sub(r'\n{3,}', '\n\n', value)
        return value.strip()

    @staticmethod
    def clean_product_desc_str(desc) ->str:
        return HTML.clean_product_desc(etree.HTML(desc)) if desc else ""
