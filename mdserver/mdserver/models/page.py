# Copyright (c) Kuba Szczodrzyński 2024-10-02.

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


class Page(BaseModel):
    # generated properties
    relpath: Path
    dirpath: Path
    source: str
    url: str
    type: str | None
    html: str | None = Field(default=None, exclude=True)
    mtime: datetime | None = None
    excerpt: str | None = None

    # metadata from frontmatter
    template: str
    title: str
    short: str | None = None
    description: str | None = None
    headline: str | None = None
    image: str | None = None
    author: str | None = None
    date: datetime | None = None
    lastmod: datetime | None = None
    draft: bool = False
    jinja: bool = False
    categories: list[str] = []
    tags: list[str] = []

    # side-by-side data
    sxs: dict | None = None
