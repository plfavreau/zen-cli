import subprocess
from pathlib import Path


class NotAWorktree(Exception):
    pass


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise NotAWorktree("not inside a git worktree")
    return result.stdout.strip()


def root() -> Path:
    return Path(_git("rev-parse", "--show-toplevel")).resolve()


def label() -> str:
    branch = _git("rev-parse", "--abbrev-ref", "HEAD")
    return root().name if branch == "HEAD" else branch
