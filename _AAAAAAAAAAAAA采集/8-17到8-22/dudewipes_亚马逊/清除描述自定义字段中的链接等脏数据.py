import argparse
import csv
import html
import re
from html.parser import HTMLParser
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = BASE_DIR / "res/dudewipes_picture.csv"
DEFAULT_OUTPUT = BASE_DIR / "data/clean.csv"

EXACT_TEXT_COLUMNS = {
    "Description",
    "anniu",
    "bubian",
    "Body (HTML)",
    "SEO Description",
    "important_information",
    "productDescription",
    "Product_details",
    "About_this_item"
}

COLUMN_KEYWORDS = (
    "description",
    "metafield",
    "miaoshu",
    "anniu",
    "bubian",
    "detail",
    "feature",
    "dimension",
    "warranty",
    "specification",
    "use and care",
)

BLOCK_DROP_TAGS = {
    "script",
    "style",
    "noscript",
    "svg",
    "select",
    "option",
    "button",
    "form",
    "iframe",
    "template",
}

ALLOW_TAGS = {
    "p",
    "br",
    "ul",
    "ol",
    "li",
    "strong",
    "b",
    "em",
    "i",
}

RAW_URL_RE = re.compile(r"https?://[^\s\"'<>]+")
EMPTY_TAG_RE = re.compile(r"<(p|li|ul|ol|strong|b|em|i)>\s*</\1>", re.I)
MULTI_BREAK_RE = re.compile(r"(?:<br>\s*){3,}", re.I)
MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")


class HtmlFieldCleaner(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.parts = []
        self.drop_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in BLOCK_DROP_TAGS:
            self.drop_depth += 1
            return
        if self.drop_depth:
            return
        if tag in ALLOW_TAGS:
            if tag == "br":
                self.parts.append("<br>")
            else:
                self.parts.append(f"<{tag}>")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in BLOCK_DROP_TAGS:
            if self.drop_depth:
                self.drop_depth -= 1
            return
        if self.drop_depth:
            return
        if tag in ALLOW_TAGS and tag != "br":
            self.parts.append(f"</{tag}>")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_data(self, data):
        if self.drop_depth:
            return
        if data:
            self.parts.append(html.escape(data, quote=False))

    def handle_entityref(self, name):
        if not self.drop_depth:
            self.parts.append(f"&{name};")

    def handle_charref(self, name):
        if not self.drop_depth:
            self.parts.append(f"&#{name};")

    def cleaned_html(self):
        return "".join(self.parts)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Clean hyperlinks and option-like HTML from description fields in a CSV."
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT),
        help="Input CSV path.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Output CSV path.",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite the input file.",
    )
    parser.add_argument(
        "--columns",
        default="",
        help="Comma-separated column names. Defaults to auto-detection.",
    )
    return parser.parse_args()


def detect_target_columns(fieldnames):
    targets = []
    for column in fieldnames:
        if column in EXACT_TEXT_COLUMNS:
            targets.append(column)
            continue

        lowered = column.lower()
        if any(keyword in lowered for keyword in COLUMN_KEYWORDS):
            targets.append(column)
    return targets


def normalize_html(text):
    value = text.replace("\r\n", "\n").replace("\r", "\n")
    value = RAW_URL_RE.sub("", value)
    value = value.replace("&nbsp;", " ")
    value = EMPTY_TAG_RE.sub("", value)
    value = MULTI_BREAK_RE.sub("<br><br>", value)
    value = MULTI_SPACE_RE.sub(" ", value)
    value = re.sub(r">\s+<", "><", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def clean_field(value):
    text = str(value or "").strip()
    if not text:
        return ""

    parser = HtmlFieldCleaner()
    parser.feed(text)
    parser.close()
    cleaned = parser.cleaned_html()
    cleaned = normalize_html(cleaned)
    return cleaned


def main():
    args = parse_args()
    input_path = Path(args.input)
    output_path = input_path if args.in_place else Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8-sig", newline="") as src:
        reader = csv.DictReader(src)
        fieldnames = reader.fieldnames or []
        target_columns = (
            [column.strip() for column in args.columns.split(",") if column.strip()]
            if args.columns.strip()
            else detect_target_columns(fieldnames)
        )

        rows = []
        changed_cells = 0
        for row in reader:
            for column in target_columns:
                if column not in row:
                    continue
                original = row.get(column, "")
                cleaned = clean_field(original)
                if cleaned != original:
                    changed_cells += 1
                row[column] = cleaned
            rows.append(row)

    with output_path.open("w", encoding="utf-8-sig", newline="") as dst:
        writer = csv.DictWriter(dst, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"input: {input_path}")
    print(f"output: {output_path}")
    print(f"columns: {', '.join(target_columns) if target_columns else 'none'}")
    print(f"rows: {len(rows)}")
    print(f"changed cells: {changed_cells}")


if __name__ == "__main__":
    main()
