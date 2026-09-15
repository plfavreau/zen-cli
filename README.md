# zen-folders

One git worktree, one Zen folder. Your coding agent opens pages into the folder for
the branch it is working on, and cleans up when the branch is done.

```bash
zen-folders open https://github.com/plfavreau/zen-folders
```

The tab lands in a folder named after your current branch.

## Setup

```bash
# 1. install
uv tool install git+https://github.com/plfavreau/zen-folders

# 2. enable it (shows a permission notice, then restart Zen once)
zen-folders setup

# 3. teach your agents
npx skills add plfavreau/zen-folders -g
```

`setup` turns on Zen's Marionette port so the CLI can talk to the browser UI. It
prints exactly what that means before changing anything, and it only runs if you
say yes.

## Commands

```
zen-folders open <url>...   open pages in this worktree's folder
zen-folders list            what is in it
zen-folders close <n|url>   drop a tab
zen-folders destroy         remove the folder and its tabs
zen-folders gc              reap folders whose worktree is gone
```

There is no way to name a folder. The CLI derives it from `git rev-parse
--show-toplevel`, so an agent can only ever touch the folder for the worktree it
is running in, and `destroy` only removes folders this tool created.

## Teardown

Call `destroy` when you delete a worktree:

```bash
cd "$worktree" && zen-folders destroy
```

Or let `gc` catch it later.

## Requirements

Zen Browser, Python 3.11 or 3.12. `setup` is macOS-only for now.

MIT.
