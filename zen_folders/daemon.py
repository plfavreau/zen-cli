"""Routes CLI commands to one persistent Marionette session shared across
invocations, instead of each command opening and closing its own connection.

Firefox resets a browsing context's form state (an input's live .value, not
its DOM attributes) the moment the Marionette connection observing it
disconnects. Every CLI command used to open a fresh connection and close it
before the command even returned to the shell, silently wiping out anything
`fill` had just set before a later `click` could ever see it. Keeping one
connection alive in a small background process avoids that disconnect
entirely.
"""

from __future__ import annotations

import fcntl
import json
import socket
import socketserver
import subprocess
import sys
import threading
import time
from contextlib import contextmanager

from . import state
from . import zen as _zen

SOCKET = state.HOME / "daemon.sock"
# Dedicated from state.locked()'s lock file: that one is already held for the
# whole session by open/close/destroy/gc, and flock() is per-open-file, not
# per-process, so acquiring it again in here would deadlock those commands.
_SPAWN_LOCK = state.HOME / "daemon-spawn.lock"

_METHODS = (
    "open",
    "list",
    "close",
    "destroy",
    "select",
    "click",
    "fill",
    "text",
    "hover",
    "key",
    "cookies",
    "network",
    "screenshot",
    "scroll",
)
_BUSINESS_ERRORS = (
    _zen.TargetNotFound,
    _zen.ElementNotFound,
    _zen.ZenUnreachable,
    _zen.InvalidKey,
)


class _Handler(socketserver.StreamRequestHandler):
    # A CLI command such as `click` sends more than one request per connection
    # (select, then the action) - the socketserver default of one request per
    # connection would close the socket after the first and break the second.
    def handle(self) -> None:
        while True:
            raw = self.rfile.readline()
            if not raw:
                return
            request = json.loads(raw)
            try:
                method = getattr(self.server.zen, request["op"])  # type: ignore[attr-defined]
                response = {"ok": True, "result": method(*request["args"])}
            except _BUSINESS_ERRORS as error:
                response = {"ok": False, "type": type(error).__name__, "message": str(error)}
            except Exception as error:
                # Anything else means the Marionette connection itself is gone (browser
                # quit, crashed). Report it, then let the daemon exit so the next CLI
                # invocation starts a fresh one instead of talking to a dead session.
                response = {"ok": False, "type": "ZenUnreachable", "message": str(error)}
                self._respond(response)
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            self._respond(response)

    def _respond(self, response: dict) -> None:
        self.wfile.write((json.dumps(response) + "\n").encode())
        self.wfile.flush()


def _serve() -> None:
    if SOCKET.exists():
        SOCKET.unlink()
    with _zen.session() as z:
        server = socketserver.UnixStreamServer(str(SOCKET), _Handler)
        server.zen = z  # type: ignore[attr-defined]
        try:
            server.serve_forever()
        finally:
            SOCKET.unlink(missing_ok=True)


def _reachable() -> bool:
    if not SOCKET.exists():
        return False
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as probe:
            probe.settimeout(0.3)
            probe.connect(str(SOCKET))
        return True
    except OSError:
        return False


def _ensure_running() -> None:
    if _reachable():
        return
    state.HOME.mkdir(parents=True, exist_ok=True)
    with _SPAWN_LOCK.open("w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            # Someone else may have won the race and started it while we waited.
            if _reachable():
                return
            subprocess.Popen(
                [sys.executable, "-m", "zen_folders.daemon"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                if _reachable():
                    return
                time.sleep(0.5)
            raise _zen.ZenUnreachable("the driver daemon did not start")
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


class _RemoteZen:
    def __init__(self, sock: socket.socket):
        self._file = sock.makefile("rwb")

    def _call(self, op: str, *args):
        self._file.write((json.dumps({"op": op, "args": args}) + "\n").encode())
        self._file.flush()
        raw = self._file.readline()
        if not raw:
            raise _zen.ZenUnreachable("the driver daemon disconnected")
        response = json.loads(raw)
        if not response["ok"]:
            error_type = getattr(_zen, response["type"], RuntimeError)
            raise error_type(response["message"])
        return response["result"]

    def __getattr__(self, name: str):
        if name not in _METHODS:
            raise AttributeError(name)
        return lambda *args: self._call(name, *args)


@contextmanager
def session():
    _ensure_running()
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(90)
    sock.connect(str(SOCKET))
    try:
        yield _RemoteZen(sock)
    finally:
        sock.close()


if __name__ == "__main__":
    _serve()
