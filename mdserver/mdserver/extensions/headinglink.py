# Copyright (c) Kuba Szczodrzyński 2024-10-07.

import re

from markdown import Extension, Markdown
from markdown.postprocessors import Postprocessor

RE_TAG_HEADING = re.compile(
    r"<h(\d)>(.+?)<\/h(\d)>",
    re.DOTALL | re.UNICODE,
)

RE_SLUG_1 = re.compile(r"[^a-z0-9-]")
RE_SLUG_2 = re.compile(r"-+")


class HeadingLinkPostprocessor(Postprocessor):
    def __init__(self, md: Markdown):
        super().__init__(md)

    def repl(self, m: re.Match):
        slug: str = m.group(2).lower()
        slug = RE_SLUG_1.sub("-", slug)
        slug = RE_SLUG_2.sub("-", slug)
        return f'<h{m.group(1)}>{m.group(2)}<a class="heading-link" href="#{slug}" id="{slug}"></a></h{m.group(3)}>'

    def run(self, text: str):
        return RE_TAG_HEADING.sub(self.repl, text)


class HeadingLinkExtension(Extension):
    def extendMarkdown(self, md: Markdown):
        md.registerExtension(self)
        md.postprocessors.register(HeadingLinkPostprocessor(md), "heading-link", 1)


def makeExtension(*args, **kwargs):
    return HeadingLinkExtension(*args, **kwargs)
