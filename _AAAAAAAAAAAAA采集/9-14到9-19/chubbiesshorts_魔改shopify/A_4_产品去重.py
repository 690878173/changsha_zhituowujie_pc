"""Merge Chubbies linked product pages before the normal SKU deduplication."""

from __future__ import annotations

import hashlib
import json
import re
from collections import OrderedDict, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlsplit, urlunsplit

import pandas as pd
from lxml import html as lxml_html

from config import Tool
from _ljp.mb.base.去重 import Quchong

input_file = Tool.File.path_add_site(r'res/result.csv')
source_file = Tool.File.path_add_site(r"res/ts_res.csv")
merged_file = Tool.File.path_add_site(r"fwq/linked_variants.csv")
output_file = Tool.File.path_add_site(r"fwq/quchong.csv")
product_group_file = Tool.File.path_add_site(r"ts/4/product_groups.json")


class ChubbiesLinkedVariantMerger:
    """Convert ProductGroup-linked URLs into normal WooCommerce families.

    The Storefront Product API only returns the native variant options for a
    URL. Chubbies publishes Color and, on some apparel, Inseam as separate
    URLs. Its product-page JSON-LD ProductGroup is the authoritative mapping
    between those URLs, even when their titles and handles have no common
    prefix. The resulting rows remain a file transform for the normal Quchong
    stage after this narrowly scoped relationship lookup.
    """

    max_attributes = 4
    request_workers = 10
    group_map_version = 4
    custom_field_marker = "(product.metafields."
    inch_pattern = re.compile(r"(?<!\d)(\d+(?:\.\d+)?)\s*(?:\"|&quot;)")

    def __init__(self, tool, input_file, output_file, product_group_file):
        self.tool = tool
        self.input_file = input_file
        self.output_file = output_file
        self.product_group_file = product_group_file

    @staticmethod
    def text(value) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @classmethod
    def normalized_url(cls, value) -> str:
        url = cls.text(value)
        if not url:
            return ""
        parsed = urlsplit(url)
        host = parsed.netloc.casefold()
        if host.startswith("www."):
            host = host[4:]
        path = parsed.path.rstrip("/") or "/"
        return urlunsplit((parsed.scheme.casefold(), host, path, "", ""))

    @staticmethod
    def option_name(value) -> str:
        text = str(value).rstrip("/").rsplit("/", 1)[-1].replace("-", " ")
        return " ".join(part.capitalize() for part in text.split())

    @classmethod
    def merge_categories(cls, values) -> str:
        merged = []
        seen = set()
        for value in values:
            for category in cls.text(value).split(","):
                category = category.strip()
                if category and category not in seen:
                    seen.add(category)
                    merged.append(category)
        return ",".join(merged)

    @classmethod
    def merge_images(cls, values, separator: str) -> str:
        merged = []
        seen = set()
        for value in values:
            for image in cls.text(value).split(separator):
                image = image.strip()
                if image and image not in seen:
                    seen.add(image)
                    merged.append(image)
        return separator.join(merged)

    @classmethod
    def source_attributes(cls, row: pd.Series) -> OrderedDict[str, str]:
        attributes = OrderedDict()
        for index in range(1, cls.max_attributes + 1):
            name = cls.text(row.get(f"Attribute {index} name", ""))
            value = cls.text(row.get(f"Attribute {index} value(s)", ""))
            if name and name.casefold() != "title" and name.casefold() not in {
                key.casefold() for key in attributes
            }:
                attributes[name] = value
        return attributes

    @classmethod
    def parent_sku(cls, product_group_id: str) -> str:
        digest = hashlib.sha1(product_group_id.encode("utf-8")).hexdigest()[:16]
        return f"linked-group-{digest}"

    @classmethod
    def linked_option_values(
        cls, tree, page_url: str
    ) -> tuple[dict[str, dict[str, str]], dict[str, str]]:
        """Read linked option values and the current PDP selection.

        Chubbies' accessible swatch label is its shopper-visible Color value:
        it preserves distinct colors and prints such as ``Navy Palms`` and
        ``Teal Stripes``.  ``data-fs-variant-value`` is only a broad color
        family (for example, ``Blue``), so it would incorrectly collapse
        sellable choices.  A discontinued source URL may redirect to a
        replacement PDP; its selected control is retained as a fallback for
        that source member.
        """
        values = {"Color": {}, "Inseam": {}}
        selected_values = {}
        selectors = (
            ("Color", "product-colors__option-link", "Swatch"),
            ("Inseam", "product-inseam__option-link", "Inseam"),
        )
        for option_name, class_name, variant_type in selectors:
            xpath = (
                '//a[@href and contains(concat(" ", normalize-space(@class), " "), '
                f'" {class_name} ")]'
            )
            for anchor in tree.xpath(xpath):
                target_url = cls.normalized_url(urljoin(page_url, anchor.get("href", "")))
                if not target_url:
                    continue
                controls = anchor.xpath(
                    './/*[@data-fs-variant-type=$variant_type]',
                    variant_type=variant_type,
                )
                if not controls:
                    continue
                control = controls[0]
                if option_name == "Color":
                    value = (
                        cls.text(control.get("aria-label"))
                        or cls.text(control.get("title"))
                        or cls.text(control.get("data-fs-variant-value"))
                    )
                else:
                    value = (
                        cls.text(control.get("data-fs-variant-value"))
                        or cls.text(control.get("aria-label"))
                        or cls.text(control.get("title"))
                    )
                if value:
                    values[option_name][target_url] = value
                    if cls.text(control.get("aria-checked")).casefold() == "true":
                        selected_values[option_name] = value
        return values, selected_values

    @classmethod
    def parse_product_group(cls, html_text: str, page_url: str) -> dict | None:
        """Read ProductGroup JSON-LD and its real product-page option labels."""
        if not html_text:
            return None
        try:
            tree = lxml_html.fromstring(html_text)
        except (TypeError, ValueError):
            return None

        product_group = None
        for script in tree.xpath('//script[@type="application/ld+json"]'):
            try:
                payload = json.loads(script.text or "")
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
            candidates = payload if isinstance(payload, list) else [payload]
            for candidate in candidates:
                if not isinstance(candidate, dict):
                    continue
                graph = candidate.get("@graph")
                nodes = graph if isinstance(graph, list) else [candidate]
                product_group = next(
                    (
                        node
                        for node in nodes
                        if isinstance(node, dict) and node.get("@type") == "ProductGroup"
                    ),
                    None,
                )
                if product_group:
                    break
            if product_group:
                break

        if not product_group:
            return None
        group_id = cls.text(product_group.get("productGroupID"))
        variants = product_group.get("hasVariant")
        if not group_id or not isinstance(variants, list):
            return None

        option_names = []
        for value in product_group.get("variesBy") or []:
            name = cls.option_name(value)
            if name and name.casefold() not in {item.casefold() for item in option_names}:
                option_names.append(name)
        linked_options, selected_options = cls.linked_option_values(tree, page_url)
        requested_url = cls.normalized_url(page_url)

        members = []
        for variant in variants:
            if not isinstance(variant, dict):
                continue
            url = cls.normalized_url(variant.get("url"))
            if not url:
                continue
            selections = {}
            for option_name in option_names:
                if option_name.casefold() == "color":
                    # JSON-LD ``color`` is the product nickname, not its
                    # actual option value.  Use the linked PDP swatch.
                    value = linked_options["Color"].get(url, "")
                    if not value and url == requested_url:
                        value = selected_options.get("Color", "")
                else:
                    key = option_name.casefold().replace(" ", "")
                    value = cls.text(variant.get(key))
                if value:
                    selections[option_name] = value
            inseam = linked_options["Inseam"].get(url, "")
            if not inseam and url == requested_url:
                inseam = selected_options.get("Inseam", "")
            if inseam:
                selections["Inseam"] = inseam
            members.append(
                {
                    "url": url,
                    "name": cls.text(variant.get("name")),
                    "selections": selections,
                }
            )

        if not members:
            return None
        cls.add_inseam_option(option_names, members)
        return {
            "id": group_id,
            "name": cls.text(product_group.get("name")),
            "option_names": option_names,
            "members": members,
        }

    @classmethod
    def add_inseam_option(cls, option_names: list[str], members: list[dict]):
        """Insert Inseam when the PDP exposes it, including a single value."""
        if any(name.casefold() == "inseam" for name in option_names):
            return
        if not any(cls.text(member.get("selections", {}).get("Inseam")) for member in members):
            # Fixed-inseam products sometimes show no selectable Inseam UI.
            # Their ProductGroup member title remains the stable fallback.
            for member in members:
                match = cls.inch_pattern.search(member.get("name", ""))
                if match:
                    member["selections"]["Inseam"] = f'{match.group(1)}"'
        if not any(cls.text(member.get("selections", {}).get("Inseam")) for member in members):
            return
        try:
            size_index = next(
                index for index, name in enumerate(option_names) if name.casefold() == "size"
            )
        except StopIteration:
            option_names.append("Inseam")
        else:
            option_names.insert(size_index, "Inseam")

    def fetch_product_group(self, url: str) -> tuple[str, dict | None, bool]:
        """Return a parsed group and whether the response is stable enough to cache."""
        try:
            response = self.tool.get(url)
            status_code = getattr(response, "status_code", 0)
            if not 200 <= status_code < 400:
                self.tool.print(
                    f"[ProductGroup] {url} returned HTTP {status_code}",
                    "yellow",
                )
                # A source route removed by the merchant remains represented
                # by related ProductGroups. Cache its 404 to avoid retrying it
                # on every pure A4 rerun; temporary failures remain retryable.
                return url, None, status_code == 404
            return url, self.parse_product_group(response.text, url), True
        except Exception as exc:
            self.tool.print(f"[ProductGroup] {url} failed: {exc}", "yellow")
            return url, None, False

    def product_groups_for_urls(self, source_urls: list[str]) -> dict[str, dict]:
        """Load or collect the relationship map needed by the A4 preprocessor."""
        saved = self.tool.File.load_json(self.product_group_file, default={})
        if not isinstance(saved, dict) or saved.get("version") != self.group_map_version:
            saved = {"version": self.group_map_version, "by_url": {}}
        by_url = saved.get("by_url")
        by_url = by_url if isinstance(by_url, dict) else {}

        missing = [url for url in source_urls if url not in by_url]
        if missing:
            self.tool.print(
                f"Collecting ProductGroup relationships for {len(missing):,} product URLs...",
                "green",
            )
            completed = 0
            with ThreadPoolExecutor(max_workers=self.request_workers) as executor:
                futures = {
                    executor.submit(self.fetch_product_group, url): url for url in missing
                }
                for future in as_completed(futures):
                    url, product_group, cacheable = future.result()
                    if cacheable:
                        by_url[url] = product_group
                    completed += 1
                    if completed % 100 == 0 or completed == len(missing):
                        self.tool.print(
                            f"ProductGroup relationships: {completed:,}/{len(missing):,}",
                            "green",
                        )
            saved["by_url"] = by_url
            self.tool.File.save_json(saved, self.product_group_file)

        return {
            url: product_group
            for url in source_urls
            if isinstance((product_group := by_url.get(url)), dict)
            and self.text(product_group.get("id"))
        }

    def deduplicate_skus(self, data: pd.DataFrame) -> pd.DataFrame:
        """Collapse category clones before building families from source URLs."""
        data = data.copy()
        parent_skus = {
            self.text(row.get("SKU", ""))
            for _, row in data[data["Type"].str.casefold() == "variable"].iterrows()
        }
        for index, row in data.iterrows():
            is_variation = self.text(row.get("Type", "")).casefold() == "variation"
            sku = self.text(row.get("SKU", ""))
            if sku and not (is_variation and sku in parent_skus):
                continue
            identity = "\x1f".join(
                self.text(row.get(column, ""))
                for column in (
                    "Parent",
                    "Name",
                    "Attribute 1 value(s)",
                    "Attribute 2 value(s)",
                    "Attribute 3 value(s)",
                    "Attribute 4 value(s)",
                    "Sale price",
                    "Images",
                )
            )
            data.at[index, "SKU"] = (
                f"missing-sku-{hashlib.sha1(identity.encode('utf-8')).hexdigest()[:16]}"
            )

        rows = []
        for _, group in data.groupby("SKU", sort=False, dropna=False):
            row = group.iloc[0].copy()
            row["Categories"] = self.merge_categories(group["Categories"])
            rows.append(row)
        return pd.DataFrame(rows, columns=data.columns)

    def families(self, data: pd.DataFrame) -> OrderedDict[str, tuple[pd.Series, list[pd.Series]]]:
        result = OrderedDict()
        variations = data[data["Type"].str.casefold() == "variation"]
        parents = data[data["Type"].str.casefold().isin(("variable", "simple"))]
        for _, parent in parents.iterrows():
            parent_sku = self.text(parent.get("SKU", ""))
            if not parent_sku:
                continue
            if self.text(parent.get("Type", "")).casefold() == "simple":
                children = []
            else:
                children = [
                    child.copy()
                    for _, child in variations[
                        variations["Parent"].map(self.text) == parent_sku
                    ].iterrows()
                ]
            result[parent_sku] = (parent.copy(), children)
        return result

    def direct_group_member(self, parent: pd.Series, groups_by_url: dict[str, dict]):
        """Use the ProductGroup declared by this URL, never another group's backlink."""
        source_url = self.normalized_url(parent.get("url", ""))
        group = groups_by_url.get(source_url)
        if not group:
            return None
        member = next(
            (
                item
                for item in group.get("members") or []
                if self.normalized_url(item.get("url", "")) == source_url
            ),
            None,
        )
        group_id = self.text(group.get("id"))
        return (group_id, group, member) if group_id and member else None

    def group_index(self, groups_by_url: dict[str, dict]):
        """Merge all PDP observations for each ProductGroup.

        Each PDP contains only a partial view of its group's linked controls.
        The relationship cache is populated concurrently, so using the first
        cached page made output depend on request completion order and dropped
        values such as a single Inseam.  Build one deterministic group map
        with selections merged by product URL before creating output families.
        """
        groups = OrderedDict()
        direct_counts = defaultdict(int)
        members_by_group = defaultdict(OrderedDict)
        source_group_ids = {}
        for source_url, group in sorted(groups_by_url.items()):
            group_id = self.text(group.get("id"))
            if not group_id:
                continue
            direct_counts[group_id] += 1
            source_group_ids[source_url] = group_id

            canonical = groups.setdefault(
                group_id,
                {
                    "id": group_id,
                    "name": self.text(group.get("name")),
                    "option_names": [],
                    "members": [],
                },
            )
            if not canonical["name"]:
                canonical["name"] = self.text(group.get("name"))
            for option_name in group.get("option_names") or []:
                option_name = self.text(option_name)
                if option_name and option_name.casefold() not in {
                    item.casefold() for item in canonical["option_names"]
                }:
                    canonical["option_names"].append(option_name)

            for member in group.get("members") or []:
                member_url = self.normalized_url(member.get("url", ""))
                if not member_url:
                    continue
                canonical_member = members_by_group[group_id].setdefault(
                    member_url,
                    {
                        "url": member_url,
                        "name": self.text(member.get("name")),
                        "selections": {},
                    },
                )
                if not canonical_member["name"]:
                    canonical_member["name"] = self.text(member.get("name"))
                for name, value in (member.get("selections") or {}).items():
                    name = self.text(name)
                    value = self.text(value)
                    if name and value and not canonical_member["selections"].get(name):
                        canonical_member["selections"][name] = value

        for group_id, group in groups.items():
            group["members"] = list(members_by_group[group_id].values())
            self.add_inseam_option(group["option_names"], group["members"])

        direct_groups = {
            source_url: groups[group_id]
            for source_url, group_id in source_group_ids.items()
        }
        return groups, direct_groups, direct_counts

    def fallback_group_member(
        self,
        parent: pd.Series,
        groups: dict[str, dict],
        direct_counts: dict[str, int],
    ):
        """Use a linked membership only when it points to a specific product group.

        A few legacy source URLs currently return no ProductGroup of their own.
        They can still be listed by a related page. Generic one-word groups
        such as ``Hat`` are category-like and must not pull unrelated products
        together; a fallback therefore needs either multiple direct
        declarations or a multi-word group name.
        """
        source_url = self.normalized_url(parent.get("url", ""))
        candidates = []
        for group_id, group in groups.items():
            member = next(
                (
                    item
                    for item in group.get("members") or []
                    if self.normalized_url(item.get("url", "")) == source_url
                ),
                None,
            )
            if not member:
                continue
            word_count = len(re.findall(r"[A-Za-z0-9]+", self.text(group.get("name"))))
            if direct_counts.get(group_id, 0) < 2 and word_count < 2:
                continue
            member_count = len(
                {
                    self.normalized_url(item.get("url", ""))
                    for item in group.get("members") or []
                    if self.normalized_url(item.get("url", ""))
                }
            )
            candidates.append((member_count, -direct_counts.get(group_id, 0), group_id, group, member))
        if not candidates:
            return None
        _, _, group_id, group, member = min(candidates, key=lambda item: item[:3])
        return group_id, group, member

    def group_member(self, parent: pd.Series, groups_by_url: dict[str, dict], groups, direct_counts):
        return self.direct_group_member(parent, groups_by_url) or self.fallback_group_member(
            parent, groups, direct_counts
        )

    def has_color_value(self, entry) -> bool:
        """Return whether a linked family member has a trustworthy Color."""
        _, parent, children, _, member = entry
        for name, value in (member.get("selections") or {}).items():
            if self.text(name).casefold() == "color" and self.text(value):
                return True
        for source_row in children or [parent]:
            for name, value in self.source_attributes(source_row).items():
                if name.casefold() == "color" and self.text(value):
                    return True
        return False

    def add_name_inseam(self, values: dict[str, str], source_row: pd.Series):
        """Recover a fixed Inseam explicitly present in the source product name."""
        if any(
            self.text(name).casefold() == "inseam" and self.text(value)
            for name, value in values.items()
        ):
            return
        match = self.inch_pattern.search(self.text(source_row.get("Name", "")))
        if match:
            values["Inseam"] = f'{match.group(1)}"'

    @classmethod
    def add_option_value(cls, values: dict[str, list[str]], name: str, value: str):
        if value and value not in values[name]:
            values[name].append(value)

    def set_attributes(self, row: pd.Series, option_names: list[str], values: dict[str, str]):
        lookup = {name.casefold(): name for name in option_names}
        normalized_values = {
            lookup[name.casefold()]: value
            for name, value in values.items()
            if name.casefold() in lookup and value
        }
        for index in range(1, self.max_attributes + 1):
            name_col = f"Attribute {index} name"
            value_col = f"Attribute {index} value(s)"
            visible_col = f"Attribute {index} visible"
            global_col = f"Attribute {index} global"
            if index <= len(option_names):
                name = option_names[index - 1]
                row[name_col] = name
                row[value_col] = normalized_values.get(name, "")
                row[visible_col] = 0
                row[global_col] = 1
            else:
                row[name_col] = ""
                row[value_col] = ""
                row[visible_col] = ""
                row[global_col] = ""

    def option_names_for_group(self, group: dict, candidates) -> list[str]:
        names = []
        for name in group.get("option_names") or []:
            name = self.text(name)
            if name and name.casefold() not in {item.casefold() for item in names}:
                names.append(name)
        observed_names = set()
        for parent, children, selections in candidates:
            source_rows = children or [parent]
            for name, value in selections.items():
                if self.text(value):
                    observed_names.add(name.casefold())
            for source_row in source_rows:
                for name, value in self.source_attributes(source_row).items():
                    if name.casefold() not in {item.casefold() for item in names}:
                        names.append(name)
                    if self.text(value):
                        observed_names.add(name.casefold())
        # Chubbies JSON-LD can list Size for a single-SKU hat. It is not a
        # sellable option until a member actually supplies a Size value.
        return [name for name in names if name.casefold() in observed_names]

    def merge_group(self, group: dict, candidates, image_separator: str) -> list[pd.Series]:
        option_names = self.option_names_for_group(group, candidates)
        group_name = self.text(group.get("name")) or self.text(candidates[0][0].get("Name", ""))
        if not group_name or len(option_names) > self.max_attributes:
            self.tool.print(
                f"[ProductGroup] skipped {group.get('id')}: {len(option_names)} attributes",
                "yellow",
            )
            return []

        parent_sku = self.parent_sku(self.text(group["id"]))
        parent = candidates[0][0].copy()
        parent["Type"] = "variable"
        parent["SKU"] = parent_sku
        parent["Name"] = group_name
        parent["Parent"] = ""
        parent["Categories"] = self.merge_categories(
            candidate[0].get("Categories", "") for candidate in candidates
        )
        parent["Images"] = self.merge_images(
            [candidate[0].get("Images", "") for candidate in candidates]
            + [child.get("Images", "") for _, children, _ in candidates for child in children],
            image_separator,
        )

        all_values = OrderedDict((name, []) for name in option_names)
        variations = []
        for source_parent, children, selections in candidates:
            source_rows = children or [source_parent]
            for source_row in source_rows:
                variation = source_row.copy()
                values = dict(selections)
                values.update(self.source_attributes(source_row))
                if any(name.casefold() == "inseam" for name in option_names):
                    self.add_name_inseam(values, source_row)
                for name in option_names:
                    value = next(
                        (
                            item_value
                            for item_name, item_value in values.items()
                            if item_name.casefold() == name.casefold()
                        ),
                        "",
                    )
                    self.add_option_value(all_values, name, self.text(value))

                variation["Type"] = "variation"
                variation["Name"] = group_name
                variation["Parent"] = parent_sku
                variation["Categories"] = parent["Categories"]
                variation["Description"] = ""
                for column in variation.index:
                    if self.custom_field_marker in column:
                        variation[column] = ""
                self.set_attributes(variation, option_names, values)
                variations.append(variation)

        self.set_attributes(
            parent,
            option_names,
            {name: ",".join(values) for name, values in all_values.items()},
        )
        return [parent, *variations]

    def merge_linked_families(self, data: pd.DataFrame, groups_by_url: dict[str, dict]) -> pd.DataFrame:
        families = self.families(data)
        groups, direct_groups, direct_counts = self.group_index(groups_by_url)
        grouped = OrderedDict()
        for sku, (parent, children) in families.items():
            resolved = self.group_member(parent, direct_groups, groups, direct_counts)
            if not resolved:
                continue
            group_id, group, member = resolved
            grouped.setdefault(group_id, []).append((sku, parent, children, group, member))

        mergeable = {}
        for group_id, entries in grouped.items():
            group = entries[0][3]
            has_color_option = any(
                self.text(name).casefold() == "color" for name in group.get("option_names") or []
            )
            eligible_entries = (
                [entry for entry in entries if self.has_color_value(entry)]
                if has_color_option
                else entries
            )
            if len(eligible_entries) > 1:
                mergeable[group_id] = eligible_entries
        image_separator = self.tool.config.images_split or ","
        output_rows = []
        emitted_groups = set()
        consumed_skus = set()

        for sku, (parent, children) in families.items():
            resolved = self.group_member(parent, direct_groups, groups, direct_counts)
            group_id = resolved[0] if resolved else ""
            if group_id in mergeable:
                entries = mergeable[group_id]
                eligible_skus = {entry_sku for entry_sku, *_ in entries}
                if sku not in eligible_skus:
                    output_rows.append(parent)
                    output_rows.extend(children)
                    consumed_skus.add(sku)
                    consumed_skus.update(
                        self.text(child.get("SKU", "")) for child in children
                    )
                    continue
                if group_id in emitted_groups:
                    continue
                candidates = [
                    (entry_parent, entry_children, entry_member.get("selections", {}))
                    for _, entry_parent, entry_children, _, entry_member in entries
                ]
                merged_rows = self.merge_group(entries[0][3], candidates, image_separator)
                if merged_rows:
                    output_rows.extend(merged_rows)
                    emitted_groups.add(group_id)
                    for entry_sku, _, entry_children, _, _ in entries:
                        consumed_skus.add(entry_sku)
                        consumed_skus.update(
                            self.text(child.get("SKU", "")) for child in entry_children
                        )
                    continue

            output_rows.append(parent)
            output_rows.extend(children)
            consumed_skus.add(sku)
            consumed_skus.update(self.text(child.get("SKU", "")) for child in children)

        output_rows.extend(
            row.copy()
            for _, row in data.iterrows()
            if self.text(row.get("SKU", "")) not in consumed_skus
        )
        output_columns = list(data.columns)
        for index in range(1, self.max_attributes + 1):
            for suffix in ("name", "value(s)", "visible", "global"):
                column = f"Attribute {index} {suffix}"
                if column not in output_columns:
                    output_columns.append(column)
        output = pd.DataFrame(output_rows, columns=output_columns)
        return output.drop(columns=["url"], errors="ignore")

    def run(self) -> pd.DataFrame:
        data = pd.read_csv(self.input_file, dtype=str, keep_default_na=False)
        required = {"Type", "SKU", "Name", "Parent", "Categories", "Images", "url"}
        missing = required.difference(data.columns)
        if missing:
            raise ValueError(f"Missing required source columns: {sorted(missing)}")

        data = self.deduplicate_skus(data)
        source_urls = list(
            OrderedDict(
                (self.normalized_url(url), None)
                for url in data["url"]
                if self.normalized_url(url)
            )
        )
        groups = self.product_groups_for_urls(source_urls)
        output = self.merge_linked_families(data, groups)
        self.tool.File.save_csv(output.to_dict("records"), self.output_file)
        self.tool.print(
            f"ProductGroup pre-merge: {len(data):,} source rows -> {len(output):,} rows; "
            f"{len({group['id'] for group in groups.values()}):,} relationship groups available.",
            "green",
        )
        return output


def main():
    # ChubbiesLinkedVariantMerger(
    #     Tool,
    #     source_file,
    #     merged_file,
    #     product_group_file,
    # ).run()
    # Preserve the existing A4 behavior after the linked-product pre-merge.
    Quchong(Tool, merged_file, output_file).run()
    Tool.close()


if __name__ == "__main__":
    # main()
    Quchong(Tool,input_file,output_file).run()
