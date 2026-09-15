from __future__ import annotations

import os
import socket
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

from marionette_driver.marionette import Marionette

from . import profile, state

ZEN = Path("/Applications/Zen.app/Contents/MacOS/zen")


class ZenUnreachable(Exception):
    pass


def _listening() -> bool:
    with socket.socket() as probe:
        probe.settimeout(0.3)
        return probe.connect_ex(("127.0.0.1", state.port())) == 0


def launch() -> None:
    if _listening():
        return
    if not ZEN.exists():
        raise ZenUnreachable(f"Zen not found at {ZEN}")
    profile.seed()
    subprocess.Popen(
        [str(ZEN), "--no-remote", "--profile", str(profile.PROFILE)],
        env={**os.environ, "MOZ_MARIONETTE": "1", "MOZ_REMOTE_ALLOW_SYSTEM_ACCESS": "1"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        if _listening():
            return
        time.sleep(1)
    raise ZenUnreachable("the agent browser did not start")


_PRELUDE = """
const norm = u => { try { return Services.io.newURI(u).spec; } catch (e) { return u; } };
const findFolder = id => gBrowser.getAllTabGroups().find(g => g.id === id) ?? null;
const urlOf = t => t.linkedBrowser?.currentURI?.spec ?? "";
const realTabs = f => f.tabs.filter(t => !t.hasAttribute("zen-empty-tab"));
"""

_OPEN = _PRELUDE + """
const resolve = arguments[arguments.length - 1];
const [folderId, label, urls] = arguments;
(async () => {
  const principal = Services.scriptSecurityManager.getSystemPrincipal();
  let folder = folderId ? findFolder(folderId) : null;
  const present = new Set(folder ? realTabs(folder).map(urlOf) : []);
  const fresh = urls.filter(u => !present.has(norm(u)));
  const tabs = fresh.map(u =>
    gBrowser.addTab(u, { triggeringPrincipal: principal, skipAnimation: true })
  );
  if (!folder) {
    folder = await gZenFolders.createFolder(tabs, { label, renameFolder: false });
  } else if (tabs.length) {
    folder.addTabs(tabs);
  }
  resolve({ id: folder.id, opened: fresh.length });
})().catch(e => resolve({ error: String(e) }));
"""

_LIST = _PRELUDE + """
const folder = findFolder(arguments[0]);
if (!folder) return null;
return realTabs(folder).map(t => ({ url: urlOf(t), title: t.label ?? "" }));
"""

_CLOSE = _PRELUDE + """
const [folderId, urls] = arguments;
const folder = findFolder(folderId);
if (!folder) return 0;
const doomed = new Set(urls.map(norm));
const victims = realTabs(folder).filter(t => doomed.has(urlOf(t)));
victims.forEach(t => gBrowser.removeTab(t));
return victims.length;
"""

_DESTROY = _PRELUDE + """
const resolve = arguments[1];
const folder = findFolder(arguments[0]);
if (!folder) return resolve(false);
folder.delete().then(() => resolve(true), () => resolve(false));
"""


class Zen:
    def __init__(self, driver: Marionette):
        self._driver = driver

    def open(self, folder_id: str | None, label: str, urls: list[str]) -> dict:
        result = self._driver.execute_async_script(
            _OPEN, script_args=[folder_id, label, urls]
        )
        if error := result.get("error"):
            raise ZenUnreachable(error)
        return result

    def list(self, folder_id: str) -> list[dict] | None:
        return self._driver.execute_script(_LIST, script_args=[folder_id])

    def close(self, folder_id: str, urls: list[str]) -> int:
        return self._driver.execute_script(_CLOSE, script_args=[folder_id, urls])

    def destroy(self, folder_id: str) -> bool:
        return self._driver.execute_async_script(_DESTROY, script_args=[folder_id])


@contextmanager
def session():
    launch()
    driver = Marionette(host="127.0.0.1", port=state.port(), socket_timeout=30)
    try:
        driver.start_session()
    except Exception as error:
        raise ZenUnreachable(
            f"no Zen listening on 127.0.0.1:{state.port()}"
        ) from error
    try:
        driver.set_context("chrome")
        yield Zen(driver)
    finally:
        driver.delete_session()
