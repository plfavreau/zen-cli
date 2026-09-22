import argparse
import base64
import sys
from pathlib import Path

from . import profile, state, worktree
from .daemon import session
from .zen import ElementNotFound, InvalidKey, TargetNotFound, ZenUnreachable, running


def _target(value: str) -> int | str:
    return int(value) - 1 if value.isdigit() else value


def _amount(value: str) -> int | str:
    try:
        return int(value)
    except ValueError:
        return value


def _where(value: str) -> str | list[int]:
    parts = value.split(",")
    if len(parts) == 2:
        try:
            return [int(parts[0]), int(parts[1])]
        except ValueError:
            pass
    return value


def _reap(zen) -> None:
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


def _click(target: str, where: str) -> None:
    record = state.get(worktree.root())
    if not record:
        return
    with session() as zen:
        url = zen.select(record["id"], _target(target))
        zen.click(url, _where(where))


def _fill(target: str, selector: str, text: str) -> None:
    record = state.get(worktree.root())
    if not record:
        return
    with session() as zen:
        url = zen.select(record["id"], _target(target))
        zen.fill(url, selector, text)


def _text(target: str, selector: str | None) -> None:
    record = state.get(worktree.root())
    if not record:
        return
    with session() as zen:
        url = zen.select(record["id"], _target(target))
        print(zen.text(url, selector))


def _hover(target: str, selector: str) -> None:
    record = state.get(worktree.root())
    if not record:
        return
    with session() as zen:
        url = zen.select(record["id"], _target(target))
        zen.hover(url, selector)


def _key(target: str, name: str) -> None:
    record = state.get(worktree.root())
    if not record:
        return
    with session() as zen:
        url = zen.select(record["id"], _target(target))
        zen.key(url, name)


def _cookies(target: str) -> None:
    record = state.get(worktree.root())
    if not record:
        return
    with session() as zen:
        url = zen.select(record["id"], _target(target))
        cookies = zen.cookies(url)
    for cookie in cookies:
        print(f"{cookie['name']}={cookie['value']}")


def _network(target: str, contains: str | None) -> None:
    record = state.get(worktree.root())
    if not record:
        return
    with session() as zen:
        url = zen.select(record["id"], _target(target))
        entries = zen.network(url, contains)
    for entry in entries:
        status = entry["status"] if entry["status"] else "cross-origin"
        print(f"{status}  {entry['duration']}ms  {entry['type']}  {entry['name']}")


def _scroll(target: str, amount: str) -> None:
    record = state.get(worktree.root())
    if not record:
        return
    with session() as zen:
        url = zen.select(record["id"], _target(target))
        zen.scroll(url, _amount(amount))


def _screenshot(target: str, path: str, selector: str | None) -> None:
    record = state.get(worktree.root())
    if not record:
        return
    with session() as zen:
        url = zen.select(record["id"], _target(target))
        data = zen.screenshot(url, selector)
    Path(path).write_bytes(base64.b64decode(data))


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


def _seed(passwords: bool) -> None:
    if running():
        print("quit the agent browser first", file=sys.stderr)
        return
    profile.seed(passwords)


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
    clicker = commands.add_parser("click", help="click an element in a tab")
    clicker.add_argument("target", help="url or list index")
    clicker.add_argument("where", help="css selector, or 'x,y' viewport coordinates")
    filler = commands.add_parser("fill", help="fill an input in a tab")
    filler.add_argument("target", help="url or list index")
    filler.add_argument("selector", help="css selector")
    filler.add_argument("text")
    texter = commands.add_parser("text", help="print an element's text, or the page's")
    texter.add_argument("target", help="url or list index")
    texter.add_argument("selector", nargs="?", help="css selector")
    hoverer = commands.add_parser("hover", help="move the pointer over an element")
    hoverer.add_argument("target", help="url or list index")
    hoverer.add_argument("selector", help="css selector")
    keyer = commands.add_parser("key", help="press a key (Enter, Escape, Tab, ArrowDown...)")
    keyer.add_argument("target", help="url or list index")
    keyer.add_argument("name", help="key name, or a single literal character")
    cookier = commands.add_parser("cookies", help="print cookies for the current page")
    cookier.add_argument("target", help="url or list index")
    networker = commands.add_parser(
        "network", help="print same-origin requests since the page loaded"
    )
    networker.add_argument("target", help="url or list index")
    networker.add_argument("contains", nargs="?", help="only requests whose url contains this")
    scroller = commands.add_parser("scroll", help="scroll the page, or an element into view")
    scroller.add_argument("target", help="url or list index")
    scroller.add_argument("amount", help="pixels (negative scrolls up), or a css selector")
    shooter = commands.add_parser("screenshot", help="save a screenshot of a tab")
    shooter.add_argument("target", help="url or list index")
    shooter.add_argument("path")
    shooter.add_argument("selector", nargs="?", help="css selector to screenshot just that element")
    commands.add_parser("destroy", help="remove this worktree's folder and its tabs")
    commands.add_parser("gc", help="remove folders whose worktree is gone")
    seeder = commands.add_parser(
        "seed", help="copy your cookies and extensions into the agent browser"
    )
    seeder.add_argument(
        "--passwords", action="store_true", help="also copy saved passwords"
    )

    args = parser.parse_args()
    actions = {
        "open": lambda: _open(args.urls),
        "list": _list,
        "close": lambda: _close(args.targets),
        "click": lambda: _click(args.target, args.where),
        "fill": lambda: _fill(args.target, args.selector, args.text),
        "text": lambda: _text(args.target, args.selector),
        "hover": lambda: _hover(args.target, args.selector),
        "key": lambda: _key(args.target, args.name),
        "cookies": lambda: _cookies(args.target),
        "network": lambda: _network(args.target, args.contains),
        "scroll": lambda: _scroll(args.target, args.amount),
        "screenshot": lambda: _screenshot(args.target, args.path, args.selector),
        "destroy": _destroy,
        "gc": _gc,
        "seed": lambda: _seed(args.passwords),
    }
    try:
        actions[args.command]()
    except (
        ZenUnreachable,
        TargetNotFound,
        ElementNotFound,
        InvalidKey,
        profile.NoProfile,
        worktree.NotAWorktree,
    ) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
