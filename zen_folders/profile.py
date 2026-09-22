"""The agent browser runs on its own profile, never the one you browse with.

It starts empty. Copying your cookies, extensions or passwords into it is an
explicit, interactive choice, because that is personal data leaving one browser
for another.
"""

import configparser
import shutil
import sys
from pathlib import Path

from . import state

PROFILE = state.HOME / "profile"

_ROOTS = [
    Path.home() / "Library/Application Support/zen",
    Path.home() / ".zen",
]

_SESSION = [
    "cookies.sqlite",
    "permissions.sqlite",
    "cert9.db",
    "containers.json",
    "handlers.json",
    "search.json.mozlz4",
    "extensions.json",
    "extension-preferences.json",
    "addonStartup.json.lz4",
    "prefs.js",
]

_PASSWORDS = ["key4.db", "logins.json"]

_DIRS = ["extensions", "browser-extension-data", "chrome"]


class NoProfile(Exception):
    pass


def source() -> Path:
    for root in _ROOTS:
        config = root / "profiles.ini"
        if not config.exists():
            continue
        parsed = configparser.ConfigParser()
        parsed.read(config)
        for section in parsed.sections():
            if section.startswith("Install") and parsed[section].get("Default"):
                return root / parsed[section]["Default"]
        for section in parsed.sections():
            if parsed[section].get("Default") == "1" and parsed[section].get("Path"):
                return root / parsed[section]["Path"]
    raise NoProfile("no Zen profile found; launch Zen once first")


def _copy(src: Path, dst: Path) -> None:
    """Databases come with their write-ahead log so SQLite can recover them."""
    for suffix in ("", "-wal", "-shm"):
        part = src.with_name(src.name + suffix)
        if part.exists():
            shutil.copy2(part, dst.with_name(dst.name + suffix))


def _write_prefs() -> None:
    (PROFILE / "user.js").write_text(
        f'user_pref("marionette.port", {state.port()});\n'
        'user_pref("browser.shell.checkDefaultBrowser", false);\n'
        # No one is ever sitting at this profile to click through a first-run tour.
        'user_pref("zen.welcome-screen.seen", true);\n'
        'user_pref("browser.aboutwelcome.enabled", false);\n'
        'user_pref("browser.preonboarding.enabled", false);\n'
    )


def ensure() -> bool:
    """True when an empty profile was just created."""
    if PROFILE.exists():
        return False
    PROFILE.mkdir(parents=True)
    _write_prefs()
    return True


def plan(passwords: bool) -> tuple[Path, list[str]]:
    src = source()
    names = [n for n in _SESSION + (_PASSWORDS if passwords else []) if (src / n).exists()]
    names += [n for n in _DIRS if (src / n).is_dir()]
    return src, names


def seed(passwords: bool = False) -> None:
    if not sys.stdin.isatty():
        raise NoProfile("run `zen-folders seed` yourself; it copies personal data")

    src, names = plan(passwords)
    print(f"copy from {src}")
    for name in names:
        print(f"  {name}")
    if passwords:
        print("\nthis includes your saved passwords.")
    if input("\ncopy these into the agent browser? [y/N] ").strip().lower() not in (
        "y",
        "yes",
    ):
        return

    if PROFILE.exists():
        shutil.rmtree(PROFILE)
    PROFILE.mkdir(parents=True)
    for name in names:
        origin = src / name
        if origin.is_dir():
            shutil.copytree(origin, PROFILE / name)
        else:
            _copy(origin, PROFILE / name)
    _write_prefs()
