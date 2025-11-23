# Copyright (c) Kuba Szczodrzyński 2024-09-27.

import re
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from .models import Page
from .util import get_page_template, get_page_type, make_url, trimtext


class Database(BaseModel):
    pages: dict[str, Page] = {}
    tree: dict[Path, dict | str] = Field(default={}, exclude=True)
    modified: bool = Field(default=False, exclude=True)

    def scan_all(self) -> None:
        from .globals import settings

        print("Scanning content")
        for path in settings.scan_paths:
            print("Scanning", path)
            self.page_scan(path)
        print("Scanning directory tree")
        self.tree_scan(settings.data_path)
        print("Scanning completed")
        self.save()

    def save(self) -> None:
        from .globals import settings

        if not self.modified:
            return
        self.modified = False
        print("Saving database")
        with open(settings.database_path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=4))

    def relpath(self, path: Path) -> tuple[Path, str]:
        from .globals import settings

        path = path.relative_to(settings.data_path)
        return path, "/".join(path.parts)

    def page_scan(self, scan_path: Path) -> None:
        from .globals import settings
        from .renderer import render_content

        for path in scan_path.glob("**/*.md"):
            render_content(None, path)
        for key, page in list(self.pages.items()):
            if not (settings.data_path / page.relpath).is_file():
                self.pages.pop(key)
                self.modified = True

    def page_get(self, *paths: Path) -> Page:
        from .globals import settings

        _, key = self.relpath(paths[0])

        # find the page in the database
        if key not in self.pages:
            return None
        page = self.pages[key]
        html_path = (settings.cache_path / page.relpath).with_suffix(".html")

        # discard if HTML older than source(s), or not existing
        try:
            st_html = html_path.stat()
        except FileNotFoundError:
            return None
        for path in paths:
            try:
                st_src = path.stat()
                if st_html.st_mtime < st_src.st_mtime:
                    return None
            except FileNotFoundError:
                continue

        # HTML is up-to-date but not in DB, read it
        if not page.html:
            with open(html_path, "r", encoding="utf-8") as f:
                page.html = f.read()

        # return a valid page with HTML
        return page

    def page_put(
        self,
        path: Path,
        html: str,
        meta: dict,
        sxs: dict | None,
    ) -> Page:
        from .globals import settings

        relpath, key = self.relpath(path)
        source = make_url(relpath, source=True)
        url = make_url(relpath)
        mtime = datetime.fromtimestamp(path.stat().st_mtime)

        # extract the default title if not provided in metadata
        if not meta.get("title"):
            match = re.search(r"<h.>.+?</h.>", html)
            if match:
                title = match.group(0)
                title = re.sub(r"<.+?>", "", title)
                title = title.replace("\n", " ")
                meta["title"] = title

        # extract a simple excerpt from the HTML
        match = re.search(r"<p>.+?<h.>", html, re.DOTALL)
        # first try matching the first paragraphs
        if match:
            excerpt = match.group(0)
        # fallback to the entire HTML, except headings
        else:
            excerpt = re.sub(r"<h.>.+?</h.>", "", html)
        # strip HTML tags and line breaks
        excerpt = re.sub(r"<.+?>", "", excerpt)
        excerpt = excerpt.replace("\n", " ")
        excerpt = trimtext(excerpt, 200, sentence=True)

        # put the excerpt as title if not found before
        if not meta.get("title"):
            meta["title"] = trimtext(excerpt, 30)

        # extract the page preview image
        if not meta.get("image", None):
            match = re.search(r'<img.+?src="(.+?)"', html)
            if match:
                meta["image"] = match.group(1)
        if "image" in meta:
            meta["image"] = make_url(relpath.parent / meta["image"])

        # extract the table of contents
        contents = []
        for match in re.finditer(r"<h(\d).*?>(.+?)<", html, re.DOTALL):
            contents.append((int(match.group(1)), match.group(2)))

        # fill in missing metadata
        if not meta.get("template"):
            meta["template"] = get_page_template(url)
        if "author" not in meta and meta.get("date"):
            # add author if it's a "post" (with at least creation date)
            meta["author"] = settings.identity.default_author

        # build the Page object
        self.pages[key] = page = Page(
            relpath=relpath,
            dirpath=relpath.parent,
            source=source,
            url=url,
            type=get_page_type(url),
            html=html,
            mtime=mtime,
            excerpt=excerpt,
            contents=contents,
            sxs=sxs,
            **meta,
        )
        self.modified = True

        # map category names
        for i, category in enumerate(page.categories):
            page.categories[i] = settings.identity.category_map.get(
                category, category.title()
            )

        # cache rendered HTML
        html_path = (settings.cache_path / relpath).with_suffix(".html")
        html_path.parent.mkdir(parents=True, exist_ok=True)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        return page

    def page_make_dummy(self, path: Path) -> Page:
        from .globals import settings

        relpath, _ = self.relpath(path)
        source = make_url(relpath, source=True)
        url = make_url(relpath)
        mtime = datetime.now()

        # create dummy metadata
        meta = dict(
            title=settings.identity.default_title,
            # author=settings.identity.default_author,
        )

        # build the Page object
        return Page(
            relpath=relpath,
            dirpath=relpath.parent,
            source=source,
            url=url,
            type=get_page_type(url),
            template=get_page_template(url),
            html=None,
            mtime=mtime,
            **meta,
        )

    def tree_scan(self, scan_path: Path, tree: dict[Path, dict | str] = None) -> None:
        from .globals import settings

        TREE_PATH_BLACKLIST = [
            settings.cache_path,
            settings.static_path,
            settings.themes_path,
            Path(__file__).parent,
        ]

        if tree is None:
            tree = self.tree
        for path in scan_path.glob("*"):
            if path.name.startswith("."):
                continue
            if path in TREE_PATH_BLACKLIST:
                continue
            relpath = path.relative_to(settings.data_path)
            if path.is_file():
                tree[relpath] = make_url(relpath)
            if path.is_dir():
                subtree = tree[relpath] = {}
                self.tree_scan(path, subtree)
