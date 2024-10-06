# Copyright (c) Kuba Szczodrzyński 2024-10-02.

import re
from pathlib import Path

from pydantic import BaseModel


class Theme(BaseModel):
    path: Path
    name: str
    replacements: list[tuple[str, str]] = []

    def process(self, html: str) -> str:
        for pattern, repl in self.replacements:
            html = re.sub(pattern, repl, html)
        return html
