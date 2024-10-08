# Copyright (c) Kuba Szczodrzyński 2024-10-07.

import re

from markdown import Extension, Markdown
from markdown.postprocessors import Postprocessor

from mdserver.util import slugify

RE_TAG_HEADING = re.compile(
    r"<h(\d)>(.+?)<\/h(\d)>",
    re.DOTALL | re.UNICODE,
)


class HeadingLinkPostprocessor(Postprocessor):
    def __init__(self, md: Markdown):
        super().__init__(md)

    def repl(self, m: re.Match):
        slug = slugify(m.group(2))
        return f'<h{m.group(1)} id="{slug}">{m.group(2)}<a class="heading-link" href="#{slug}"></a></h{m.group(3)}>'

    def run(self, text: str):
        return RE_TAG_HEADING.sub(self.repl, text)


class HeadingLinkExtension(Extension):
    def extendMarkdown(self, md: Markdown):
        md.registerExtension(self)
        md.postprocessors.register(HeadingLinkPostprocessor(md), "heading-link", 1)


def makeExtension(*args, **kwargs):
    return HeadingLinkExtension(*args, **kwargs)
