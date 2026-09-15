"""The agent profile is seeded from the real one so logins carry over."""

from __future__ import annotations

import configparser
import shutil
from pathlib import Path

from . import state

PROFILE = state.HOME / "profile"

_ROOTS = [Path.home() / "Library/Application Support/zen", Path.home() / ".zen"]

_FILES = [
    "cookies.sqlite",
    "key4.db",
    "logins.json",
    "cert9.db",
    "permissions.sqlite",
    "containers.json",
    "handlers.json",
    "search.json.mozlz4",
    "extensions.json",
    "extension-preferences.json",
    "addonStartup.json.lz4",
    "prefs.js",
]

_DIRS = ["extensions", "browser-extension-data", "chrome"]


class NoProfile(Exception):
    pass


def source() -> Path:
    for root in _ROOTS:
        ini = root / "profiles.ini"
        if not ini.exists():
            continue
        parser = configparser.ConfigParser()
        parser.read(ini)
        for name in parser.sections():
            if name.startswith("Install") and parser[name].get("Default"):
                return root / parser[name]["Default"]
        for name in parser.sections():
            if parser[name].get("Default") == "1" and parser[name].get("Path"):
                return root / parser[name]["Path"]
    raise NoProfile("no Zen profile found")


def _copy(src: Path, dst: Path) -> None:
    """Databases come with their write-ahead log so SQLite can recover them."""
    for suffix in ("", "-wal", "-shm"):
        part = src.with_name(src.name + suffix)
        if part.exists():
            shutil.copy2(part, dst.with_name(dst.name + suffix))


def seed(force: bool = False) -> None:
    if PROFILE.exists() and not force:
        return
    src = source()
    if PROFILE.exists():
        shutil.rmtree(PROFILE)
    PROFILE.mkdir(parents=True)
    for name in _FILES:
        origin = src / name
        if origin.exists():
            _copy(origin, PROFILE / name)
    for name in _DIRS:
        origin = src / name
        if origin.exists():
            shutil.copytree(origin, PROFILE / name, dirs_exist_ok=True)
    (PROFILE / "user.js").write_text(
        f'user_pref("marionette.port", {state.port()});\n'
        'user_pref("browser.shell.checkDefaultBrowser", false);\n'
    )
