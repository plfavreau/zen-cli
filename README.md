# zen-folders

One git worktree, one [Zen Browser](https://zen-browser.app) folder.

Your coding agent opens the docs it read, the PR it created, and the ticket it worked
from into a Zen folder named after your branch. When the worktree goes away, so does
the folder.

```
zen-folders open https://docs.example.com/api   # lands in folder "feat/payments"
zen-folders list
zen-folders destroy
```

## Why it is not an MCP server

The agent needs four verbs, not forty tools. A CLI plus a skill costs the agent a few
lines of context instead of a schema dump, and it works from a shell script, a git
hook, or a Makefile just as well as from an agent.

## Scoping

The CLI accepts no folder identifier. Ever. It derives the folder from
`git rev-parse --show-toplevel` and looks that path up in `~/.zen-folders/state.json`.
An agent working in one worktree has no syntax available to touch another worktree's
folder. `destroy` only removes folders this tool recorded creating, so folders you
made by hand are untouchable even if the labels collide.

## Install

```bash
uv tool install git+https://github.com/plfavreau/zen-folders
zen-folders setup
```

`setup` explains what it is about to enable, asks once, then pins a Marionette port in
your Zen profile and installs a launch agent exporting `MOZ_MARIONETTE=1` and
`MOZ_REMOTE_ALLOW_SYSTEM_ACCESS=1`. Restart Zen once and you are done.

## What setup actually enables

Zen folders are not web content — they are browser UI, built by a privileged global
called `gZenFolders`. Reaching it needs Marionette's chrome context, and Gecko will
only grant that to a browser started with system access allowed.

That means an unauthenticated, chrome-privileged execution socket on loopback, in the
browser you are logged into everything with. Any process running as you can drive it.
Such a process could already read your cookies and SSH keys off disk, so this is an
escalation in degree rather than in kind — but it is a real one. Decide deliberately.

If you would rather not, point the tool at a dedicated profile instead. You lose the
thing that makes it useful: the folders appear in a browser you do not browse in.

Marionette cannot be switched on at runtime — `startAtRuntime` is gated behind a pref
that ships disabled with no callers — so the one restart is unavoidable.

## Agent setup

Copy `skills/zen-folders` into `.claude/skills/` or `.opencode/skills/`.

For automatic teardown, call `zen-folders destroy` wherever you remove worktrees.

## Requirements

Zen Browser, Python 3.11 or 3.12, macOS (Linux works, but `setup` is macOS-only —
export the two variables yourself).

## License

MIT
