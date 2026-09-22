---
name: zen-cli
description: Keep the pages behind a coding session in a Zen browser folder, and drive them - click, fill, scroll, read text, check a network request, screenshot what rendered. Use when a page is worth keeping (the PR you opened, the ticket you are implementing, documentation that drove a decision) or when you need to verify something in a real browser (does a fix actually render, did a login flow work, did that request succeed). Triggers on "open this in my browser", "put that in my Zen folder", "show me the docs you used", "check if this works in the browser", "click that for me", and on opening a PR.
---

# zen-cli

Every worktree gets one folder in the human's browser, named after the branch.
You cannot name another one and there is no reason to ask which — there is only
yours.

## Commands

```bash
zen-cli open <url>...              # open pages in this worktree's folder
zen-cli list                       # what is in it
zen-cli close <url|#>              # drop a tab, by url or by its number in list
zen-cli click <url|#> <css|x,y>    # click an element, or exact viewport coordinates
zen-cli fill <url|#> <css> <text>  # fill an input
zen-cli text <url|#> [css]         # read an element's text, or the page's
zen-cli hover <url|#> <css>        # move the pointer over an element
zen-cli key <url|#> <name>         # press a key: Enter, Escape, Tab, ArrowDown...
zen-cli cookies <url|#>            # print cookies for the current page
zen-cli network <url|#> [substring]  # print same-origin requests since load
zen-cli scroll <url|#> <px|css>    # scroll by pixels, or an element into view
zen-cli screenshot <url|#> <path> [css]  # screenshot the screen, or just one element
zen-cli destroy                    # remove the folder and its tabs
```

`open` is idempotent: a page already in the folder is not opened twice. Silence
means success.

`click`/`fill`/`text`/`hover`/`key`/`scroll`/`screenshot`/`cookies`/`network`
let you drive a page, not just look at it — fill and submit a form, click
through a flow, read back a result, screenshot what rendered, check whether
a request even succeeded. Address the tab the same way as `close`: by its
url or its number in `list`. A `fill` in one command and a `click` in a later
one see the same value; a background daemon keeps one connection to the tab
alive across commands specifically so this works.

`network` shows url, type, duration and real HTTP status for same-origin
requests since the page loaded — including failures, so `network 1 api/`
after a `click` is how you check whether the request that click triggered
actually succeeded. Cross-origin requests print as `cross-origin` instead of
a status; the browser hides that detail from the page unless the target
server opts in, not something workaroundable from here. No headers, no
bodies, no interception — that is a different, much bigger kind of tool.

`key` presses a named key (`Enter`, `Escape`, `Tab`, `ArrowDown`, ...) or a
single literal character for anything not in that list — useful to submit a
form with Enter instead of hunting for a submit button's selector, or to
close a modal with Escape. `hover` is the pointer-only version of `click`,
for menus and tooltips that only reveal on mouseover.

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
Give `screenshot` a selector to capture just one element instead of the
whole screen.

## When to open a page

- The PR you just created.
- The ticket you are implementing.
- Documentation that decided something — the page you would cite in review.
- A failing CI run or a dashboard the human will want to look at.

## When to drive a page

- Confirming a fix actually renders, instead of trusting the diff.
- Walking a login or checkout flow to see where it actually breaks.
- Reading back the result of an action the human asked you to verify.
- Checking whether a request a click triggered actually succeeded.

## When not to

- Pages you fetched only to quote back.
- Throwaway lookups and search results.
- Anything the human did not ask about and would not think to check.

A folder with four pages that matter is useful. One with forty is noise.

## The folder is not in the everyday browser

Pages open in a second Zen running on its own profile, which starts empty. A
page behind a login wall will show a sign-in screen, and that is expected. Do
not try to log in. Mention that `zen-cli seed` copies the human's cookies
across, and that they have to run it themselves.

## Teardown

When the work is finished and the worktree is going away:

```bash
zen-cli destroy
```

## If it fails

Report the error line and move on. Opening a browser tab is not the task and
never a blocker.
