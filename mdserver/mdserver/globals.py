# Copyright (c) Kuba Szczodrzyński 2024-10-03.

import json
from os import getenv, makedirs
from os.path import dirname
from pathlib import Path

from fastapi.templating import Jinja2Templates
from pymdownx import emoji

from .database import Database
from .models import Settings, Theme
from .util import load

# load settings file location from environment, fallback to __file__/../../../
settings_dir = getenv("SETTINGS_DIR", dirname(dirname(dirname(__file__))))
settings_dir_path = Path(settings_dir).resolve()
# prepare settings file paths, with dynamically chosen extension
settings_paths = [
    settings_dir_path / "settings.___",
    settings_dir_path / "settings.site.___",
    settings_dir_path / "settings.env.___",
]
# load data from all settings files
settings_data = {}
for path in settings_paths:
    settings_data.update(load(path))
# build the settings object
settings = Settings(**settings_data)

# initialize paths in settings
settings.data_path = (settings_dir_path / settings.data_path).resolve()
settings.cache_path = (settings_dir_path / settings.cache_path).resolve()
settings.static_path = (settings_dir_path / settings.static_path).resolve()
settings.themes_path = (settings_dir_path / settings.themes_path).resolve()
for i, path in enumerate(settings.scan_paths):
    settings.scan_paths[i] = (settings_dir_path / path).resolve()
# ensure directories exist
for path in [
    settings.data_path,
    settings.cache_path,
    settings.static_path,
    settings.themes_path,
] + settings.scan_paths:
    makedirs(path, exist_ok=True)
# initialize misc settings
settings.extension_configs.get("pymdownx.emoji", {})["emoji_index"] = emoji.twemoji
settings.extension_configs.get("pymdownx.emoji", {})["emoji_generator"] = emoji.to_png

# load the database
try:
    with open(settings.database_path, "r", encoding="utf-8") as f:
        database = Database(**json.load(f))
except Exception as e:
    print(e)
    database = Database()

# load the templates
templates = Jinja2Templates(directory=settings.themes_path)

# keep loaded themes
themes: dict[str, Theme] = {}


def get_theme(name: str):
    global themes
    if name in themes:
        return themes[name]
    theme_path = settings.themes_path / name / "theme.___"
    try:
        print("Loading theme", name)
        theme = Theme(path=theme_path.parent, name=name, **load(theme_path))
    except FileNotFoundError:
        theme = Theme(path=theme_path.parent, name=name)
    themes[name] = theme
    return theme
