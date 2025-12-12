# Copyright (c) Kuba Szczodrzyński 2023-05-10.

from mimetypes import guess_type
from pathlib import Path

import yaml
import yaml_include
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from .globals import database, settings
from .renderer import render_content, render_page
from .util import get_page_template_virtual, make_url

app = FastAPI()
app.mount(settings.static_url, StaticFiles(directory=settings.static_path), "static")
app.mount(settings.themes_url, StaticFiles(directory=settings.themes_path), "themes")
database.scan_all()
yaml.add_constructor(
    tag="!include",
    constructor=yaml_include.Constructor(base_dir=settings.data_path),
    Loader=yaml.SafeLoader,
)


@app.get("/{path_str:path}")
async def root(
    request: Request,
    path_str: str,
):
    index_suffix = ["", ".html"]

    relpath = Path(path_str)
    path = Path(settings.data_path, relpath)

    if not path.is_relative_to(settings.data_path):
        # prevent path traversal
        return Response(status_code=400)
    if any(p.startswith(".") for p in path.parts):
        # prevent access to hidden files/directories
        return Response(status_code=400)

    url = make_url(relpath, index=index_suffix)
    query = "?" + str(request.query_params) if request.query_params else ""

    # redirect index requests
    if path.stem in settings.index_names and path.suffix in index_suffix:
        return RedirectResponse(url + query)

    # handle directory requests
    if path.is_dir():
        # redirect directories with a trailing slash
        if path_str and not path_str.endswith("/"):
            return RedirectResponse("/" + path_str + "/" + query)
        # find the index file
        for index in settings.index_names:
            if (path / f"{index}.md").is_file():
                path = path / f"{index}.html"
                break
        else:
            path = path / "index.html"
        # apppend index name to path vars
        path_str = path_str.rstrip("/") + "/" + path.name
        relpath = relpath / path.name
        url = make_url(relpath)

    # serve all real files
    if path.is_file():
        # redirect files without a trailing slash
        if path_str and path_str.endswith("/"):
            return RedirectResponse("/" + path_str.rstrip("/") + query)
        # guess media type by extension
        media_type = guess_type(path)[0]
        # if not found, try to detect by first 1024 bytes
        if not media_type:
            with path.open("rb") as f:
                header = f.read(1024)
            if b"\x00" in header:
                media_type = "application/octet-stream"
            else:
                media_type = "text/plain"
        return FileResponse(path, media_type=media_type)

    # serve Markdown files
    if path.suffix in index_suffix and path.with_suffix(".md").is_file():
        # redirect files without a trailing slash
        # only allow requesting Markdown by .html suffix
        if path.suffix != ".html" or path_str and path_str.endswith("/"):
            return RedirectResponse(make_url(relpath.with_suffix(".html")) + query)
        path = path.with_suffix(".md")
        page = render_content(request, path)
        database.save()
        return render_page(request, page)

    # serve template-only pages
    if template := get_page_template_virtual(url):
        # redirect files without a trailing slash
        if path.suffix != "" and path_str and path_str.endswith("/"):
            return RedirectResponse("/" + path_str.rstrip("/") + query)
        # redirect directories with a trailing slash
        if path.suffix == "" and path_str and not path_str.endswith("/"):
            return RedirectResponse("/" + path_str + "/" + query)
        # create a dummy Page
        page = database.page_make_dummy(path)
        page.template = template
        return render_page(request, page)

    return JSONResponse(str((path, url)), status_code=404)
