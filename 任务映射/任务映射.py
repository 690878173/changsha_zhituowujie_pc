"""任务映射：扫描 ``_AAAAAAAAAAAAA采集``，按日期维护站点进度表。

扫描规则：只取两层名字 —— ``_AAAAAAAAAAAAA采集/<日期>/<站点文件夹>``，
不进入站点文件夹内部；跳过 ``_`` / ``.`` 开头的目录（例如 ``__pycache__``）
和普通文件。

数据文件是同目录的 ``站点 映射表.json``，日期是第一层键：

    {
      "8-31到9-5": {
        "nodpod_shopify": {"下载图片": 0, "完成流程": 0, "上传": 0}
      },
      "9-14到9-19": {}
    }

- 第一层：日期目录名（扫描出来的，也可自己加），按日期排序
- 第二层：站点名称，块内按名字排序，加站点只要在这里加一行
- 三个标记取值 0/1；重复扫描不会覆盖已有值，只有新站点按 ``--初始值`` 补齐
- 旧结构（站点为第一层、带 ``时间`` 列表）首次运行会自动转换过来

常用命令：
    python 任务映射.py                                   # 扫描并更新映射表
    python 任务映射.py --预演                             # 只看会改什么，不写文件
    python 任务映射.py 标记 --日期 8-31到9-5 --上传 1      # 按日期整批打标
    python 任务映射.py 标记 --站点 nodpod_shopify --下载图片 1
    python 任务映射.py 新增 --日期 9-14到9-19 --站点 newsite_shopify --下载图片 1
    python 任务映射.py 查看 --日期 8-31到9-5
    python 任务映射.py 汇总
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
SCAN_ROOT = REPO_ROOT / '_AAAAAAAAAAAAA采集'
MAPPING_PATH = BASE_DIR / '站点 映射表.json'

TIME_FIELD = '时间'
FLAG_FIELDS = ('下载图片', '完成流程', '上传')
_UNKNOWN_DATE = (99, 99)
_DAY_RE = re.compile(r'^(\d{1,2})-(\d{1,2})')
_RANGE_RE = re.compile(r'^(\d{1,2})-(\d{1,2})\s*(?:到|-|~)\s*(\d{1,2})-(\d{1,2})')


# ── 名字 / 值处理 ───────────────────────────────────────
def date_key(name):
    """排序用的 (月, 日)，例如 ``8-31到9-5`` -> (8, 31)。"""
    match = _DAY_RE.match(str(name or '').strip())
    return (int(match.group(1)), int(match.group(2))) if match else _UNKNOWN_DATE


def date_range(name):
    """日期段 ``8-31到9-5`` -> ((8, 31), (9, 5))；``8-3之前`` -> (None, (8, 3))。"""
    text = str(name or '').strip()
    match = _RANGE_RE.match(text)
    if match:
        start = (int(match.group(1)), int(match.group(2)))
        end = (int(match.group(3)), int(match.group(4)))
        return start, end
    single = _DAY_RE.match(text)
    if not single:
        return None
    day = (int(single.group(1)), int(single.group(2)))
    if text.endswith('之前'):
        return None, day
    if text.endswith(('之后', '以后')):
        return day, None
    return day, day


def resolve_day(day, known_days):
    """把 ``9-15`` 这种日期归到所在日期段（``9-14到9-19``）；找不到就原样保留。"""
    day = str(day or '').strip()
    if not day:
        return ''
    if day in known_days:
        return day
    target = date_key(day)
    if target == _UNKNOWN_DATE:
        return day
    for candidate in sorted(known_days, key=lambda name: (date_key(name), name)):
        span = date_range(candidate)
        if not span:
            continue
        start, end = span
        if (start is None or start <= target) and (end is None or target <= end):
            return candidate
    return day


def flag_value(value):
    """把 1/0、是/否、true/false 统一成 1/0。"""
    if isinstance(value, bool):
        return 1 if value else 0
    text = str(value).strip().lower()
    if text in {'1', '是', 'y', 'yes', 'true', 't'}:
        return 1
    if text in {'0', '否', 'n', 'no', 'false', 'f', ''}:
        return 0
    raise ValueError(f'无法识别的标记值: {value!r}（请用 1/0）')


def new_entry(initial=0, **flags):
    """新建一个站点条目，值统一成 0/1。"""
    entry = {field: initial for field in FLAG_FIELDS}
    for field, value in flags.items():
        if field in FLAG_FIELDS and value is not None:
            entry[field] = flag_value(value)
    return entry


def is_site_dir(path):
    """站点文件夹：目录，且名字不以 ``_`` / ``.`` 开头。"""
    return path.is_dir() and not path.name.startswith(('_', '.'))


def _width(text):
    return sum(2 if unicodedata.east_asian_width(char) in 'WF' else 1 for char in str(text))


def _pad(text, size):
    text = str(text)
    return text + ' ' * max(size - _width(text), 1)


# ── 扫描 ────────────────────────────────────────────────
def scan(root=SCAN_ROOT):
    """返回 (``{日期目录名: [站点名, ...]}``, 空日期目录列表)。"""
    root = Path(root)
    if not root.is_dir():
        raise FileNotFoundError(f'采集目录不存在: {root}')

    by_day = {}
    empty_dates = []
    day_dirs = sorted(
        (item for item in root.iterdir() if item.is_dir() and not item.name.startswith(('_', '.'))),
        key=lambda item: (date_key(item.name), item.name),
    )
    for day_dir in day_dirs:
        sites = sorted(item.name for item in day_dir.iterdir() if is_site_dir(item))
        by_day[day_dir.name] = sites
        if not sites:
            empty_dates.append(day_dir.name)
    return by_day, empty_dates


# ── 映射表读写 ──────────────────────────────────────────
def load_mapping(path=MAPPING_PATH):
    path = Path(path)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f'读取映射表失败: {path}: {exc}') from exc
    if not isinstance(data, dict):
        raise ValueError(f'映射表顶层必须是对象: {path}')
    return data


def save_mapping(data, path=MAPPING_PATH):
    """原子写入，避免写到一半留下坏文件。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle_fd, temp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=f'.{path.name}.', suffix='.tmp'
    )
    try:
        with os.fdopen(handle_fd, 'w', encoding='utf-8') as handle:
            json.dump(order_mapping(data), handle, ensure_ascii=False, indent=2)
            handle.write('\n')
        os.replace(temp_name, path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise
    return path


def order_mapping(data):
    """日期键按日期排序，站点键按名字排序。"""
    ordered = {}
    for day in sorted(data, key=lambda name: (date_key(name), str(name))):
        bucket = data[day]
        if isinstance(bucket, dict):
            ordered[day] = {site: bucket[site] for site in sorted(bucket, key=str)}
        else:
            ordered[day] = bucket
    return ordered


def is_site_shape(value):
    """旧结构判断：这个值看起来像「站点 -> 时间 + 三个标记」。"""
    return isinstance(value, dict) and (
        TIME_FIELD in value or any(field in value for field in FLAG_FIELDS)
    )


def migrate_site_keyed(data, known_days):
    """把「站点为第一层」的旧结构转换成「日期为第一层」。"""
    if not any(is_site_shape(value) for value in data.values()):
        return data, 0
    converted = {}
    moved = 0
    for site, record in data.items():
        if not is_site_shape(record):
            converted.setdefault(str(site), entry)
            continue
        days = [day for day in (record.get(TIME_FIELD) or []) if day] or ['']
        extra = {
            key: value for key, value in record.items()
            if key != TIME_FIELD and key not in FLAG_FIELDS
        }
        flags = {field: record.get(field, 0) for field in FLAG_FIELDS}
        for raw_day in days:
            day = resolve_day(raw_day, known_days) or '未标日期'
            bucket = converted.setdefault(day, {})
            entry = new_entry(**flags)
            entry.update(extra)
            bucket[str(site)] = entry
            moved += 1
    return converted, moved


def merge_scan(data, by_day, initial=0):
    """把扫描结果并进映射表，返回新增的 (日期, 站点) 列表。"""
    added = []
    for day, sites in by_day.items():
        bucket = data.get(day)
        if not isinstance(bucket, dict):
            bucket = {}
            data[day] = bucket
        for site in sites:
            entry = bucket.get(site)
            if not isinstance(entry, dict):
                bucket[site] = new_entry(initial)
                added.append((day, site))
            else:
                for field in FLAG_FIELDS:
                    entry.setdefault(field, initial)
    return added


# ── 修改 ────────────────────────────────────────────────
def mark(data, sites=None, days=None, every=False, **flags):
    """给指定日期块里的站点写标记，返回被改动的 (日期, 站点)。"""
    wanted = {str(site).strip() for site in (sites or []) if str(site).strip()}
    changed = []
    for day, bucket in data.items():
        if not isinstance(bucket, dict):
            continue
        if days and day not in days:
            continue
        for site, entry in bucket.items():
            if not every and wanted and site not in wanted:
                continue
            if not isinstance(entry, dict):
                continue
            for field, value in flags.items():
                if field in FLAG_FIELDS and value is not None:
                    entry[field] = flag_value(value)
            changed.append((day, site))
    if not changed:
        raise ValueError('没有匹配到任何站点，请检查 --日期 / --站点')
    return changed


def add_site(data, day, site, **flags):
    """手工新增一个站点条目（日期块不存在会自动建）。"""
    day, site = str(day).strip(), str(site).strip()
    if not day or not site:
        raise ValueError('日期和站点都不能为空')
    bucket = data.get(day)
    if not isinstance(bucket, dict):
        bucket = {}
        data[day] = bucket
    if site in bucket and isinstance(bucket[site], dict):
        entry = bucket[site]
        for field, value in flags.items():
            if field in FLAG_FIELDS and value is not None:
                entry[field] = flag_value(value)
    else:
        bucket[site] = new_entry(**flags)
    for field in FLAG_FIELDS:
        bucket[site].setdefault(field, 0)
    return day, site


def rename(data, old, new, days=None):
    """把某日期块里的站点改名；目标已存在时合并（标记取较大值）。"""
    old, new = str(old).strip(), str(new).strip()
    moved = []
    for day, bucket in data.items():
        if not isinstance(bucket, dict) or old not in bucket:
            continue
        if days and day not in days:
            continue
        source = bucket.pop(old)
        target = bucket.get(new)
        if isinstance(target, dict) and isinstance(source, dict):
            for field in FLAG_FIELDS:
                target[field] = max(
                    flag_value(target.get(field, 0)), flag_value(source.get(field, 0))
                )
            for key, value in source.items():
                target.setdefault(key, value)
        else:
            bucket[new] = source
        moved.append((day, new))
    if not moved:
        raise KeyError(f'没有找到站点: {old}')
    return moved


# ── 展示 ────────────────────────────────────────────────
def rows_for(data, day=None, site=None):
    rows = []
    for day_name, bucket in order_mapping(data).items():
        if day and day_name != day:
            continue
        if not isinstance(bucket, dict):
            continue
        for site_name, entry in bucket.items():
            if site and site_name != site:
                continue
            if isinstance(entry, dict):
                rows.append([
                    day_name, site_name,
                    *(entry.get(field, 0) for field in FLAG_FIELDS),
                ])
    return rows


def print_rows(rows, headers=('日期', '站点', *FLAG_FIELDS)):
    if not rows:
        print('（没有匹配的记录）')
        return
    widths = [
        max(_width(headers[index]), *(_width(row[index]) for row in rows)) + 2
        for index in range(len(headers))
    ]
    print(''.join(_pad(headers[i], widths[i]) for i in range(len(headers))).rstrip())
    for row in rows:
        print(''.join(_pad(row[i], widths[i]) for i in range(len(headers))).rstrip())


def print_scan(by_day, empty_dates):
    for day in sorted(by_day, key=lambda name: (date_key(name), name)):
        sites = by_day[day]
        note = '（空目录）' if not sites else '：' + '、'.join(sites)
        print(f'{_pad(day, 16)} {len(sites):>2} 个站点 {note}')
    total = sum(len(sites) for sites in by_day.values())
    print(f'合计 {total} 个站点文件夹、{len(by_day)} 个日期目录')


def print_summary(data):
    rows = []
    for day in sorted(data, key=lambda name: (date_key(name), str(name))):
        bucket = data[day]
        if not isinstance(bucket, dict):
            rows.append([day, 0, 0, 0, 0])
            continue
        rows.append([
            day,
            len(bucket),
            *(
                sum(1 for entry in bucket.values()
                    if isinstance(entry, dict) and flag_value(entry.get(field, 0)))
                for field in FLAG_FIELDS
            ),
        ])
    print_rows(rows, headers=('日期', '站点数', *FLAG_FIELDS))
    print(
        '合计',
        sum(row[1] for row in rows),
        '站点，',
        ' / '.join(f'{field} {sum(row[2 + index] for row in rows)}'
                   for index, field in enumerate(FLAG_FIELDS)),
    )


# ── 命令行 ──────────────────────────────────────────────
def _add_flag_args(parser):
    for field in FLAG_FIELDS:
        parser.add_argument(f'--{field}', dest=field, nargs='?', const=1, default=None,
                            type=flag_value, help='1 或 0')


def build_parser():
    parser = argparse.ArgumentParser(description='扫描 _AAAAAAAAAAAAA采集，按日期维护站点映射表')
    parser.add_argument('--采集目录', '--root', dest='root', default=str(SCAN_ROOT))
    parser.add_argument('--映射', '--mapping', dest='mapping', default=str(MAPPING_PATH))
    parser.add_argument('--预演', '--dry-run', dest='dry', action='store_true', help='只打印，不写文件')
    parser.add_argument('--初始值', dest='initial', type=flag_value, default=0,
                        help='新站点三个标记的初始值，默认 0')
    sub = parser.add_subparsers(dest='command')

    mark_parser = sub.add_parser('标记', aliases=['mark'], help='给站点写 0/1 标记')
    mark_parser.add_argument('--日期', '--date', dest='day', action='append', default=None)
    mark_parser.add_argument('--站点', '--site', dest='site', action='append', default=None)
    mark_parser.add_argument('--全部', '--all', dest='every', action='store_true')
    _add_flag_args(mark_parser)

    add_parser = sub.add_parser('新增', aliases=['add'], help='手工加一个站点')
    add_parser.add_argument('--日期', '--date', dest='day', required=True)
    add_parser.add_argument('--站点', '--site', dest='site', required=True)
    _add_flag_args(add_parser)

    rename_parser = sub.add_parser('改名', aliases=['rename'], help='改站点名并合并')
    rename_parser.add_argument('--从', '--from', dest='old', required=True)
    rename_parser.add_argument('--到', '--to', dest='new', required=True)
    rename_parser.add_argument('--日期', '--date', dest='day', action='append', default=None)

    view_parser = sub.add_parser('查看', aliases=['list'], help='按日期或站点查看')
    view_parser.add_argument('--日期', '--date', dest='day', default=None)
    view_parser.add_argument('--站点', '--site', dest='site', default=None)

    sub.add_parser('汇总', aliases=['summary'], help='按日期统计进度')
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    mapping_path = Path(args.mapping)
    data = load_mapping(mapping_path)

    if args.command in (None, '更新', 'update'):
        by_day, empty_dates = scan(args.root)
        data, moved = migrate_site_keyed(data, set(by_day))
        added = merge_scan(data, by_day, initial=args.initial)
        print_scan(by_day, empty_dates)
        if moved:
            print(f'旧结构转换：{moved} 条站点记录已归入对应日期')
        print(f'新增 {len(added)} 个站点')
        if added:
            print('新增：' + '、'.join(f'{day}/{site}' for day, site in added))
        if args.dry:
            print(f'[预演] 未写入 {mapping_path}')
        else:
            print(f'已写入 {save_mapping(data, mapping_path)}')
        return 0

    if args.command in ('标记', 'mark'):
        flags = {field: getattr(args, field) for field in FLAG_FIELDS}
        if all(value is None for value in flags.values()):
            parser.error('至少要给一个标记，例如 --上传 1')
        changed = mark(data, sites=args.site, days=args.day, every=args.every, **flags)
        if not args.dry:
            save_mapping(data, mapping_path)
        else:
            print(f'[预演] 未写入 {mapping_path}')
        print_rows(rows_for(data, day=(args.day or [None])[0], site=(args.site or [None])[0]))
        print(f'已标记 {len(changed)} 条记录')
        return 0

    if args.command in ('新增', 'add'):
        day, site = add_site(
            data, args.day, args.site,
            **{field: getattr(args, field) for field in FLAG_FIELDS},
        )
        if not args.dry:
            save_mapping(data, mapping_path)
        print_rows(rows_for(data, day=day, site=site))
        return 0

    if args.command in ('改名', 'rename'):
        moved = rename(data, args.old, args.new, days=args.day)
        if not args.dry:
            save_mapping(data, mapping_path)
        print_rows([row for row in rows_for(data, site=args.new)])
        print(f'已改名 {len(moved)} 条记录')
        return 0

    if args.command in ('查看', 'list'):
        print_rows(rows_for(data, day=args.day, site=args.site))
        return 0

    if args.command in ('汇总', 'summary'):
        print_summary(data)
        return 0

    parser.print_help()
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
