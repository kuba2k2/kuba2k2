# Copyright (c) Kuba Szczodrzyński 2024-09-27.

import json
import re
from pathlib import Path

import frontmatter
import markdown
import yaml
from fastapi import Request
from fastapi.responses import HTMLResponse, Response
from jinja2 import FileSystemLoader, Template

from . import util
from .globals import database, get_theme, settings
from .models import Page


def render_context(
    request: Request | None,
    page: Page | dict | None,
    html: str | None,
    sxs: dict | None,
) -> dict:
    return dict(
        **__builtins__,
        # global vars
        settings=settings,
        identity=settings.identity,
        database=database,
        util=util,
        # local vars
        request=request,
        page=page,
        html=html,
        sxs=sxs or isinstance(page, Page) and page.sxs or {},
        query=request and request.query_params,
    )


def render_content(request: Request, path: Path) -> Page:
    # make side-by-side data paths
    sxs_json = path.with_suffix(".json")
    sxs_yaml = path.with_suffix(".yaml")

    # return if page already rendered and loaded/cached
    page = database.page_get(path, sxs_json, sxs_yaml)
    force_render = request and request.query_params.get("force")
    if page and not force_render:
        return page

    print("Rendering", path)

    # otherwise read the source file
    with open(path, "r", encoding="utf-8") as f:
        post = frontmatter.load(f)
        md = post.content
        meta = post.metadata

    # load side-by-side data
    sxs = None
    if sxs_json.is_file():
        sxs = json.loads(sxs_json.read_text("utf-8"))
    elif sxs_yaml.is_file():
        sxs = yaml.load(sxs_yaml.read_text("utf-8"), yaml.SafeLoader)
    # make it into a dict
    if isinstance(sxs, list):
        sxs = dict(enumerate(sxs))

    # apply Markdown substitutions
    md = re.sub(r"]\((.*?)\.md\)", r"](\1.html)", md)

    # render the page as template, if necessary
    if meta.get("jinja"):
        context = render_context(
            request=None,
            page=meta,
            html=None,
            sxs=sxs,
        )
        template = Template(md)
        md = template.render(context)

    extension_configs = {
        "pymdownx.snippets": {
            "base_path": [str(path.parent)],
        }
    }

    # render the page to HTML
    html = markdown.markdown(
        text=md,
        extensions=settings.extensions,
        extension_configs=settings.extension_configs | extension_configs,
    )

    # cache the result and store in database
    return database.page_put(path, html, meta, sxs)


def render_page(request: Request, page: Page) -> Response:
    theme = get_theme(settings.identity.default_theme)

    context = render_context(
        request=request,
        page=page,
        html=theme.process(page.html or ""),
        sxs=None,
    )

    template_path = settings.data_path / page.dirpath / "template.html"
    if page.template and page.template.startswith("./"):
        template_path = settings.data_path / page.dirpath / page.template
    elif not template_path.is_file():
        template_path = theme.path / f"{page.template}.html"

    # fallback to default if template does not exist
    if not template_path.is_file():
        print(f"Template '{template_path}' is not a file, falling back to default")
        template_path = theme.path / "default.html"

    # render and serve the template response
    template = Template(template_path.read_text())
    template.environment.loader = FileSystemLoader(settings.themes_path)
    html = template.render(context)
    return HTMLResponse(html)
