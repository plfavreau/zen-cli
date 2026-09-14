---
name: zen-folders
description: Keep the pages you are working from in a Zen Browser folder tied to the current git worktree, so the human can see and reuse your browsing. Use when you consult documentation, open a pull request, read a ticket, or land on a page the human will want after you stop. Triggers on "open this in my browser", "put that in my Zen folder", "show me the docs you used".
---

# zen-folders

Every git worktree gets one Zen folder. You act on the folder for the worktree you
are standing in — there is no way to name another one, and no reason to ask which.

## Commands

```
zen-folders open <url> [<url>...]   # open urls in this worktree's folder
zen-folders list                    # url and title, one tab per line
zen-folders close <url|index>       # drop tabs
zen-folders destroy                 # remove the folder and its tabs
```

`open` is idempotent: a url already in the folder is not opened twice. Silence means
success — only `list` prints on the happy path.

## When to open a page

- Documentation you actually read to make a decision.
- The pull request once you create it.
- The ticket or issue driving the work.
- A dashboard, log view, or failing CI run the human will want to look at.

## When not to

- Throwaway lookups you resolved in one glance.
- Anything you fetched only to quote back into the conversation.
- Pages behind a login the human has not mentioned.

Err on the side of fewer tabs. The folder is a handover, not a history.

## Teardown

Run `zen-folders destroy` when the worktree's work is finished and merged. If the
worktree is deleted without it, the folder is reaped on the next command.

## If it fails

`no Zen listening on 127.0.0.1:<port>` means the human has not run `zen-folders setup`
or has not restarted Zen since. Report that line and move on — it is not your task to
fix, and it does not block the work.
