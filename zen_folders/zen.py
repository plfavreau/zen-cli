from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

from marionette_driver.by import By
from marionette_driver.errors import NoSuchElementException
from marionette_driver.marionette import Marionette

from . import profile, state

ZEN = Path("/Applications/Zen.app/Contents/MacOS/zen")


class ZenUnreachable(Exception):
    pass


class TargetNotFound(Exception):
    pass


class ElementNotFound(Exception):
    pass


def running() -> bool:
    with socket.socket() as probe:
        probe.settimeout(0.3)
        return probe.connect_ex(("127.0.0.1", state.port())) == 0


def launch() -> None:
    if running():
        return
    if not ZEN.exists():
        raise ZenUnreachable(f"Zen not found at {ZEN}")
    if profile.ensure():
        print(
            "started an empty agent browser; `zen-folders seed` copies your logins",
            file=sys.stderr,
        )
    subprocess.Popen(
        [str(ZEN), "--no-remote", "--profile", str(profile.PROFILE)],
        env={**os.environ, "MOZ_MARIONETTE": "1", "MOZ_REMOTE_ALLOW_SYSTEM_ACCESS": "1"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        if running():
            return
        time.sleep(1)
    raise ZenUnreachable("the agent browser did not start")


_PRELUDE = """
const norm = u => { try { return Services.io.newURI(u).spec; } catch (e) { return u; } };
const findFolder = id => gBrowser.getAllTabGroups().find(g => g.id === id) ?? null;
const urlOf = t => {
  const live = t.linkedBrowser?.currentURI?.spec ?? "";
  if (live && live !== "about:blank") return live;
  return t.getAttribute("zen-folders-url") || live;
};
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
  const tabs = fresh.map(u => {
    const tab = gBrowser.addTab(u, { triggeringPrincipal: principal, skipAnimation: true });
    tab.setAttribute("zen-folders-url", u);
    return tab;
  });
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

_SELECT = _PRELUDE + """
const [folderId, indexOrUrl] = arguments;
const folder = findFolder(folderId);
if (!folder) return null;
const tabs = realTabs(folder);
const tab = typeof indexOrUrl === "number"
  ? tabs[indexOrUrl]
  : tabs.find(t => urlOf(t) === norm(indexOrUrl));
if (!tab) return null;
gBrowser.selectedTab = tab;
return urlOf(tab);
"""

# Dispatched in-page rather than via WebDriver's native click/send_keys, which require
# the tab to actually be the OS-focused window and fail otherwise (agents usually drive
# tabs in the background).
_CLICK = "document.querySelector(arguments[0]).click();"

_FILL = """
const el = document.querySelector(arguments[0]);
el.focus();
el.value = arguments[1];
el.dispatchEvent(new Event("input", { bubbles: true }));
el.dispatchEvent(new Event("change", { bubbles: true }));
"""

_TEXT = "return document.querySelector(arguments[0]).innerText;"


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

    def select(self, folder_id: str, target: int | str) -> str:
        url = self._driver.execute_script(_SELECT, script_args=[folder_id, target])
        if url is None:
            raise TargetNotFound(f"no such tab: {target!r}")
        return url

    def click(self, url: str, selector: str) -> None:
        with self._content(url) as driver:
            self._find(driver, selector)
            driver.execute_script(_CLICK, script_args=[selector])

    def fill(self, url: str, selector: str, text: str) -> None:
        with self._content(url) as driver:
            self._find(driver, selector)
            driver.execute_script(_FILL, script_args=[selector, text])

    def text(self, url: str, selector: str | None) -> str:
        with self._content(url) as driver:
            if selector:
                self._find(driver, selector)
                return driver.execute_script(_TEXT, script_args=[selector])
            return driver.execute_script("return document.body.innerText")

    def screenshot(self, url: str) -> str:
        with self._content(url) as driver:
            return driver.screenshot()

    @staticmethod
    def _find(driver: Marionette, selector: str):
        try:
            return driver.find_element(By.CSS_SELECTOR, selector)
        except NoSuchElementException as error:
            raise ElementNotFound(f"no element matching {selector!r}") from error

    @contextmanager
    def _content(self, url: str):
        driver = self._driver
        driver.set_context("content")
        try:
            # driver.get_url() can lag right after a session attaches; document.URL is live.
            current = driver.execute_script("return document.URL")
            if current.rstrip("/") != url.rstrip("/"):
                driver.navigate(url)
            yield driver
        finally:
            driver.set_context("chrome")


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
