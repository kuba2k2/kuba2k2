# Copyright (c) Kuba Szczodrzyński 2023-05-10.

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .globals import database, settings
from .renderer import render_content, render_page
from .util import get_page_template_virtual, make_url

app = FastAPI()
app.mount(settings.static_url, StaticFiles(directory=settings.static_path), "static")
app.mount(settings.themes_url, StaticFiles(directory=settings.themes_path), "themes")
database.scan_all()


@app.get("/{path_str:path}")
async def root(
    request: Request,
    path_str: str,
):
    index_suffix = ["", ".html"]

    relpath = Path(path_str)
    path = Path(settings.data_path, relpath)
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
        return FileResponse(path)

    # serve Markdown files
    if path.suffix in index_suffix and path.with_suffix(".md").is_file():
        # redirect files without a trailing slash
        # only allow requesting Markdown by .html suffix
        if path.suffix != ".html" or path_str and path_str.endswith("/"):
            return RedirectResponse(make_url(relpath.with_suffix(".html")) + query)
        path = path.with_suffix(".md")
        page = render_content(path)
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
