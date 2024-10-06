# Copyright (c) Kuba Szczodrzyński 2024-09-27.

from pathlib import Path

from pydantic import BaseModel, Extra


class Settings(BaseModel):
    class Identity(BaseModel, extra=Extra.allow):
        default_author: str = "Me"
        default_title: str = "Page"
        default_theme: str = "bootstrap"
        category_map: dict[str, str] = {}

    data_path: Path
    cache_path: Path

    static_path: Path = Path(__file__).parents[2] / "static"
    static_url: str = "/static"
    themes_path: Path = Path(__file__).parents[2] / "static/themes"
    themes_url: str = "/static/themes"

    extensions: list[str] = []
    extension_configs: dict = {}
    page_template_map: dict[str, str] = {}
    page_type_map: dict[str, str] = {}
    index_names: list[str] = ["index", "README"]
    per_page: int = 10
    scan_paths: list[Path] = []

    identity: Identity = Identity()

    @property
    def database_path(self) -> Path:
        return self.cache_path / "database.json"
