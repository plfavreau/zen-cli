# zen-folders

One git worktree, one Zen folder.

```bash
zen-folders open https://github.com/plfavreau/zen-folders/pull/1
```

The tab lands in a folder named after your current branch, in a Zen window
dedicated to your coding sessions. Your everyday browser is never touched.

## Setup

```bash
uv tool install git+https://github.com/plfavreau/zen-folders   # 1. install
npx skills add plfavreau/zen-folders -g                        # 2. teach your agents
```

That is all. The first `open` starts a second Zen on an empty profile at
`~/.zen-folders/profile`. It knows nothing about you until you say otherwise.

```bash
zen-folders seed              # copy your cookies and extensions across
zen-folders seed --passwords  # and your saved passwords
```

`seed` lists exactly what it will copy and asks before touching anything. It
only runs from a terminal, never from an agent. Quit the agent browser first.

## Commands

```bash
zen-folders open <url>...   # open pages in this worktree's folder
zen-folders list            # what is in it
zen-folders close <url|#>   # drop a tab
zen-folders destroy         # remove the folder and its tabs
zen-folders gc              # remove folders whose worktree is gone
zen-folders seed            # copy your cookies and extensions across
```

There is no way to name a folder. The one you get is derived from
`git rev-parse --show-toplevel`, so an agent can only ever touch the folder of
the worktree it is working in, and `destroy` only removes folders this tool
created.

## Teardown

```bash
cd "$worktree" && zen-folders destroy
```

Or let `gc` catch it later if the worktree is already gone.

## Why a second browser

Zen folders are browser UI, and only privileged code inside Zen can create
them. Reaching that code means enabling Marionette, which makes the browser
announce itself as automated — enough for Cloudflare and friends to block it.
Running that on your daily profile breaks the sites you actually use, so
zen-folders runs its own.

That profile starts empty. Your cookies and passwords are personal data, so
moving them into a second browser is something you ask for, not something a
tool does on your behalf while opening a tab.

## Requirements

Zen, and Python 3.11 or 3.12.

## License

MIT
