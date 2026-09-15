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

That is all. The first `open` copies your cookies, logins and extensions into a
dedicated profile at `~/.zen-folders/profile` and starts a second Zen with it,
so you are already signed in to the sites you use.

## Commands

```bash
zen-folders open <url>...   # open pages in this worktree's folder
zen-folders list            # what is in it
zen-folders close <url|#>   # drop a tab
zen-folders destroy         # remove the folder and its tabs
zen-folders gc              # remove folders whose worktree is gone
zen-folders reseed          # refresh the copied logins
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

`reseed` refreshes the copy when you have signed in to something new. Quit the
agent browser first.

## Requirements

Zen, and Python 3.11 or 3.12.

## License

MIT
