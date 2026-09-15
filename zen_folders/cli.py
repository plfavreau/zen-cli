import argparse
import sys

from . import profile, state, worktree
from .zen import Zen, ZenUnreachable, session


def _reap(zen: Zen) -> None:
    for path, record in state.orphans():
        zen.destroy(record["id"])
        state.forget(path)


def _open(urls: list[str]) -> None:
    root = worktree.root()
    label = worktree.label()
    with state.locked(), session() as zen:
        _reap(zen)
        record = state.get(root)
        result = zen.open(record["id"] if record else None, label, urls)
        state.remember(root, result["id"], label)


def _list() -> None:
    record = state.get(worktree.root())
    if not record:
        return
    with session() as zen:
        tabs = zen.list(record["id"])
    for index, tab in enumerate(tabs or [], start=1):
        print(f"{index}  {tab['url']}  {tab['title']}".rstrip())


def _close(targets: list[str]) -> None:
    root = worktree.root()
    record = state.get(root)
    if not record:
        return
    with state.locked(), session() as zen:
        tabs = zen.list(record["id"]) or []
        urls = {
            tabs[int(t) - 1]["url"] if t.isdigit() and 0 < int(t) <= len(tabs) else t
            for t in targets
        }
        zen.close(record["id"], sorted(urls))


def _destroy() -> None:
    root = worktree.root()
    record = state.get(root)
    if not record:
        return
    with state.locked(), session() as zen:
        zen.destroy(record["id"])
    state.forget(root)


def _gc() -> None:
    if not state.orphans():
        return
    with state.locked(), session() as zen:
        _reap(zen)


def _reseed() -> None:
    """Quit the agent browser first; a live profile cannot be replaced."""
    profile.seed(force=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="zen-folders", description="One git worktree, one Zen folder."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    opener = commands.add_parser("open", help="open urls in this worktree's folder")
    opener.add_argument("urls", nargs="+")
    commands.add_parser("list", help="list tabs in this worktree's folder")
    closer = commands.add_parser("close", help="close tabs by url or list index")
    closer.add_argument("targets", nargs="+")
    commands.add_parser("destroy", help="remove this worktree's folder and its tabs")
    commands.add_parser("gc", help="remove folders whose worktree is gone")
    commands.add_parser("reseed", help="refresh the agent browser's logins")

    args = parser.parse_args()
    actions = {
        "open": lambda: _open(args.urls),
        "list": _list,
        "close": lambda: _close(args.targets),
        "destroy": _destroy,
        "gc": _gc,
        "reseed": _reseed,
    }
    try:
        actions[args.command]()
    except (ZenUnreachable, profile.NoProfile, worktree.NotAWorktree) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
