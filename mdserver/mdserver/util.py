# Copyright (c) Kuba Szczodrzyński 2024-10-01.

import json
import re
from collections import defaultdict
from datetime import date, datetime
from math import ceil
from pathlib import Path
from urllib.parse import parse_qsl, urlencode
from zlib import crc32

import yaml

from .models import Page

RE_SLUG_1 = re.compile(r"[^a-z0-9-]")
RE_SLUG_2 = re.compile(r"-+")


def load(path: Path) -> dict | list | str:
    json_path = path.with_suffix(".json")
    if json_path.is_file():
        return json.loads(json_path.read_text("utf-8")) or {}
    yaml_path = path.with_suffix(".yaml")
    if yaml_path.is_file():
        return yaml.load(yaml_path.read_text("utf-8"), yaml.SafeLoader) or {}
    return path.read_text("utf-8")


def make_url(
    relpath: Path,
    source: bool = False,
    index: list[str] = [".md", ".html"],
) -> str:
    from .globals import settings

    # make any absolute paths relative
    if relpath.is_absolute():
        relpath = relpath.relative_to(settings.data_path)
    # eliminate ".." components
    relpath = relpath.resolve().relative_to(Path.cwd())

    # return raw URLs for source files
    if source:
        return "/" + "/".join(relpath.parts)

    # return directory URLs for index files
    if relpath.stem in settings.index_names and relpath.suffix in index:
        if len(relpath.parent.parts):
            return "/" + "/".join(relpath.parent.parts) + "/"
        else:
            return "/"

    # return directory URLs for paths without suffix
    if relpath.suffix == "":
        if len(relpath.parts):
            return "/" + "/".join(relpath.parts) + "/"
        else:
            return "/"

    # return HTML URLs for Markdown files
    if relpath.suffix == ".md":
        return "/" + "/".join(relpath.with_suffix(".html").parts)

    # return raw URLs for everything else
    return "/" + "/".join(relpath.parts)


def get_page_type(url: str) -> str:
    from .globals import settings

    for pattern, type in settings.page_type_map.items():
        if re.fullmatch(pattern, url):
            return type
    url = url.lstrip("/")
    if not url:
        return "index"
    return None


def get_page_template(url: str) -> str | None:
    from .globals import settings

    for pattern, template in settings.page_template_map.items():
        pattern = pattern.lstrip("!")
        if re.fullmatch(pattern, url):
            return template
    url = url.lstrip("/")
    if not url:
        return "index"
    return url.partition("/")[0]


def get_page_template_virtual(url: str) -> str | None:
    from .globals import settings

    for pattern, template in settings.page_template_map.items():
        if pattern.startswith("!"):
            continue
        if re.fullmatch(pattern, url):
            return template
    return None


def trimtext(text: str, length: int, sentence: bool = False) -> str:
    # trim a string, breaking on word boundary
    words = text.split(" ")
    text = ""
    for word in words:
        text += word + " "
        if len(text) >= length or sentence and word[-1:] in ".?!":
            break
    # append an ellipsis if needed
    text = text.strip(" ,:/")
    if text[-1:] in ".?!":
        return text
    return text + "..."


def intsafe(value: str, default: int = 0) -> int:
    try:
        return int(value or default)
    except ValueError:
        return default


def datefmt(dt: datetime) -> str:
    if not dt:
        return ""
    return dt.strftime("%B %d, %Y").replace(" 0", " ")


def monthfmt(dt: datetime) -> str:
    if not dt:
        return ""
    return dt.strftime("%B %Y")


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = RE_SLUG_1.sub("-", text)
    text = RE_SLUG_2.sub("-", text)
    return text.strip("-")


def hashchoice(value, choices: list):
    return choices[crc32(str(value).encode()) % len(choices)]


def group_by_month(pages: list[Page]) -> list[tuple[date, int]]:
    out = defaultdict(int)
    for page in pages:
        if not page.date:
            continue
        date = page.date.date().replace(day=1)
        out[date] += 1
    return sorted(out.items(), reverse=True)


def group_by_category(pages: list[Page]) -> list[tuple[str, int]]:
    out = defaultdict(int)
    for page in pages:
        for category in page.categories:
            out[category] += 1
    return sorted(out.items())


def group_by_tag(pages: list[Page], count: int) -> list[tuple[str, int]]:
    out = defaultdict(int)
    count_max = 0
    for page in pages:
        for tag in page.tags:
            out[tag] += 1
            count_max = max(count_max, out[tag])
    out = sorted(sorted(out.items(), key=lambda tpl: -tpl[1])[0:count])
    return [(k, v * 9 // count_max) for k, v in out]


FILTER_PARAMS = [
    ("Year", "year"),
    ("Month", "month"),
    ("Author", "author"),
    ("Category", "category"),
    ("Tag", "tag"),
    ("Searching for", "q"),
]


def filtered(pages: list[Page], query: dict | None, *types: str) -> list[Page]:
    # filter pages by type, sort by date
    pages = sorted(
        filter(lambda p: p.type in types and not p.draft, pages),
        key=lambda p: p.date and p.date.timestamp() or 0.0,
        reverse=True,
    )
    if not query:
        return pages
    # apply filters from query parameters
    year = intsafe(query.get("year"))
    month = intsafe(query.get("month"))
    author = query.get("author")
    series = query.get("series")
    category = query.get("category")
    tag = query.get("tag")
    query.get("q")
    if year:
        pages = [page for page in pages if page.date and page.date.year == year]
    if month:
        pages = [page for page in pages if page.date and page.date.month == month]
    if author:
        pages = [page for page in pages if page.author == author]
    if series:
        pages = [page for page in pages if page.series == series]
    if category:
        pages = [page for page in pages if category in page.categories]
    if tag:
        pages = [page for page in pages if tag in page.tags]
    return pages


def paged(pages: list[Page], query: dict) -> list[Page]:
    from .globals import settings

    page = intsafe(query.get("page"), 1)
    return pages[(page - 1) * settings.per_page : page * settings.per_page]


def pagination(count: int, page: int) -> list[int]:
    from .globals import settings

    total_pages = ceil(count / settings.per_page)
    if total_pages <= 1:
        return []
    page = intsafe(page, 1)
    min_page = max(page - 2, 1)
    max_page = min(page + 2, total_pages)
    nums = range(min_page, max_page + 1)
    out = []
    if 1 not in nums:
        out.append(1)
        if 2 not in nums:
            out.append(0)
    out += nums
    if total_pages not in nums:
        if total_pages - 1 not in nums:
            out.append(0)
        out.append(total_pages)
    return out


def querymod(query: dict, **params) -> str:
    qs = dict(parse_qsl(str(query)))
    for key, value in params.items():
        if value is None:
            qs.pop(key, None)
        else:
            qs[key] = str(value)
    if "page" not in params:
        qs.pop("page", None)
    return "?" + urlencode(qs)
