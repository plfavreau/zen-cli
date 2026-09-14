import configparser
import platform
import subprocess
from pathlib import Path

from . import state

PROFILE_ROOTS = [
    Path.home() / "Library/Application Support/zen",
    Path.home() / ".zen",
]

AGENT = Path.home() / "Library/LaunchAgents/com.plfavreau.zen-folders.plist"

MARKER = "# managed by zen-folders"

WARNING = """zen-folders drives Zen through Marionette, which means enabling
unauthenticated, chrome-privileged script execution on 127.0.0.1:{port}
in the browser you are logged into everything with.

Any process running as you can then drive that browser. Such a process
could already read your cookies and SSH keys off disk; this escalates it
to live session control. Decide if that trade is acceptable.
"""


class SetupError(Exception):
    pass


def default_profile() -> Path:
    for root in PROFILE_ROOTS:
        ini = root / "profiles.ini"
        if not ini.exists():
            continue
        parser = configparser.ConfigParser()
        parser.read(ini)
        for section in parser.sections():
            if section.startswith("Install") and (path := parser[section].get("Default")):
                return root / path
        for section in parser.sections():
            if parser[section].get("Default") == "1" and (path := parser[section].get("Path")):
                return root / path
    raise SetupError("no Zen profile found — launch Zen once, then retry")


def pin_port(profile: Path, port: int) -> None:
    user_js = profile / "user.js"
    kept = [
        line
        for line in (user_js.read_text().splitlines() if user_js.exists() else [])
        if MARKER not in line
    ]
    kept.append(f'user_pref("marionette.port", {port}); {MARKER}')
    user_js.write_text("\n".join(kept) + "\n")


def install_agent(port: int) -> None:
    if platform.system() != "Darwin":
        raise SetupError(
            "automatic setup is macOS-only; export MOZ_MARIONETTE=1 and "
            "MOZ_REMOTE_ALLOW_SYSTEM_ACCESS=1 before launching Zen"
        )
    AGENT.parent.mkdir(parents=True, exist_ok=True)
    AGENT.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.plfavreau.zen-folders</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/sh</string>
    <string>-c</string>
    <string>launchctl setenv MOZ_MARIONETTE 1; launchctl setenv MOZ_REMOTE_ALLOW_SYSTEM_ACCESS 1</string>
  </array>
  <key>RunAtLoad</key><true/>
</dict>
</plist>
"""
    )
    subprocess.run(["launchctl", "unload", str(AGENT)], capture_output=True, check=False)
    subprocess.run(["launchctl", "load", str(AGENT)], capture_output=True, check=True)


def run() -> None:
    port = state.port()
    print(WARNING.format(port=port))
    if input("Enable it? [y/N] ").strip().lower() not in {"y", "yes"}:
        raise SetupError("aborted")
    profile = default_profile()
    pin_port(profile, port)
    install_agent(port)
    state.HOME.mkdir(parents=True, exist_ok=True)
    if not state.CONFIG.exists():
        state.CONFIG.write_text(f"port = {port}\n")
    print(f"profile: {profile}")
    print("restart Zen once, then `zen-folders open <url>`")
