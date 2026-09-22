import fcntl
import json
import os
import tomllib
from contextlib import contextmanager
from pathlib import Path

HOME = Path(os.environ.get("ZEN_CLI_HOME", Path.home() / ".zen-cli"))
STATE = HOME / "state.json"
CONFIG = HOME / "config.toml"
LOCK = HOME / "lock"

DEFAULT_PORT = 2830


def port() -> int:
    if env := os.environ.get("ZEN_CLI_PORT"):
        return int(env)
    if CONFIG.exists():
        return int(tomllib.loads(CONFIG.read_text()).get("port", DEFAULT_PORT))
    return DEFAULT_PORT


@contextmanager
def locked():
    HOME.mkdir(parents=True, exist_ok=True)
    with LOCK.open("w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _read() -> dict[str, dict]:
    if not STATE.exists():
        return {}
    return json.loads(STATE.read_text()).get("folders", {})


def _write(folders: dict[str, dict]) -> None:
    HOME.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({"folders": folders}, indent=2) + "\n")


def get(worktree: Path) -> dict | None:
    return _read().get(str(worktree))


def remember(worktree: Path, folder_id: str, label: str) -> None:
    folders = _read()
    folders[str(worktree)] = {"id": folder_id, "label": label}
    _write(folders)


def forget(worktree: Path) -> None:
    folders = _read()
    folders.pop(str(worktree), None)
    _write(folders)


def orphans() -> list[tuple[Path, dict]]:
    return [
        (Path(path), record)
        for path, record in _read().items()
        if not Path(path).exists()
    ]
