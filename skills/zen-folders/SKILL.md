---
name: zen-folders
description: Keep the pages behind a coding session in a Zen browser folder, so the human can see what you read and what you built. Use when a page is worth keeping - the PR you opened, the ticket you are implementing, documentation that drove a decision, a dashboard the human will want to check. Triggers on "open this in my browser", "put that in my Zen folder", "show me the docs you used", and on opening a PR.
---

# zen-folders

Every worktree gets one folder in the human's browser, named after the branch.
You cannot name another one and there is no reason to ask which — there is only
yours.

## Commands

```bash
zen-folders open <url>...              # open pages in this worktree's folder
zen-folders list                       # what is in it
zen-folders close <url|#>              # drop a tab, by url or by its number in list
zen-folders click <url|#> <css|x,y>    # click an element, or exact viewport coordinates
zen-folders fill <url|#> <css> <text>  # fill an input
zen-folders text <url|#> [css]         # read an element's text, or the page's
zen-folders scroll <url|#> <px|css>    # scroll by pixels, or an element into view
zen-folders screenshot <url|#> <path>  # save a screenshot
zen-folders destroy                    # remove the folder and its tabs
```

`open` is idempotent: a page already in the folder is not opened twice. Silence
means success.

`click`/`fill`/`text`/`scroll`/`screenshot` let you drive a page, not just
look at it — fill and submit a form, click through a flow, read back a
result, screenshot what rendered. Address the tab the same way as `close`: by
its url or its number in `list`. A `fill` in one command and a `click` in a
later one see the same value; a background daemon keeps one connection to the
tab alive across commands specifically so this works.

`click`/`fill` are real WebDriver interactions, not scripted ones: a click
auto-scrolls its target into view for you, so you do not need `scroll` just
to reach something below the fold. Reach for `scroll` only when the page
itself needs to see you scroll: content gated behind `IntersectionObserver`
(lazy-loaded images, infinite-scroll feeds) will not load until the viewport
actually reaches it. `scroll 1 400` moves the viewport by pixels (negative
scrolls up); `scroll 1 ".next-page"` scrolls an element into view instead.

`click`'s target is a css selector by default, or `x,y` viewport coordinates
for something without a reliable selector — a canvas, a chart, anything you
only know the position of. `click 1 "400,300"` clicks exactly there.

Clicking a link that navigates elsewhere is not reflected in a later
`list`/`close` by URL — address that tab by its `list` index afterwards
instead, since Firefox does not reliably update a tab's tracked location for
a page-driven cross-origin navigation.

`open` raises the browser window when it first starts, so a `screenshot` shows
the page the way a person would actually see it. If the human covers it with
another window later, screenshots go back to an unrendered fallback until it
is brought forward again — not something you can fix from inside the page.

## When to open a page

- The PR you just created.
- The ticket you are implementing.
- Documentation that decided something — the page you would cite in review.
- A failing CI run or a dashboard the human will want to look at.

## When not to

- Pages you fetched only to quote back.
- Throwaway lookups and search results.
- Anything the human did not ask about and would not think to check.

A folder with four pages that matter is useful. One with forty is noise.

## The folder is not in the everyday browser

Pages open in a second Zen running on its own profile, which starts empty. A
page behind a login wall will show a sign-in screen, and that is expected. Do
not try to log in. Mention that `zen-folders seed` copies the human's cookies
across, and that they have to run it themselves.

## Teardown

When the work is finished and the worktree is going away:

```bash
zen-folders destroy
```

## If it fails

Report the error line and move on. Opening a browser tab is not the task and
never a blocker.
