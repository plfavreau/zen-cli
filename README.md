# zen-cli

One git worktree, one Zen folder you can drive.

```bash
zen-cli open https://github.com/plfavreau/zen-cli/pull/1
```

The tab lands in a folder named after your current branch, in a Zen window
dedicated to your coding sessions. Your everyday browser is never touched.

## Setup

```bash
uv tool install git+https://github.com/plfavreau/zen-cli   # 1. install
npx skills add plfavreau/zen-cli -g                         # 2. teach your agents
```

That is all. The first `open` starts a second Zen on an empty profile at
`~/.zen-cli/profile`. It knows nothing about you until you say otherwise.

```bash
zen-cli seed              # copy your cookies and extensions across
zen-cli seed --passwords  # and your saved passwords
```

`seed` lists exactly what it will copy and asks before touching anything. It
only runs from a terminal, never from an agent. Quit the agent browser first.

## Commands

```bash
zen-cli open <url>...            # open pages in this worktree's folder
zen-cli list                     # what is in it
zen-cli close <url|#>            # drop a tab
zen-cli click <url|#> <css|x,y>  # click an element, or exact viewport coordinates
zen-cli fill <url|#> <css> <text>  # fill an input in a tab
zen-cli text <url|#> [css]       # read an element's text, or the page's
zen-cli hover <url|#> <css>      # move the pointer over an element
zen-cli key <url|#> <name>       # press a key: Enter, Escape, Tab, ArrowDown...
zen-cli cookies <url|#>          # print cookies for the current page
zen-cli network <url|#> [substring]  # print same-origin requests since load
zen-cli scroll <url|#> <px|css>  # scroll by pixels, or an element into view
zen-cli screenshot <url|#> <path> [css]  # screenshot the screen, or just one element
zen-cli destroy                  # remove the folder and its tabs
zen-cli gc                       # remove folders whose worktree is gone
zen-cli seed                     # copy your cookies and extensions across
```

There is no way to name a folder. The one you get is derived from
`git rev-parse --show-toplevel`, so an agent can only ever touch the folder of
the worktree it is working in, and `destroy` only removes folders this tool
created.

`click`/`fill`/`text`/`hover`/`key`/`scroll`/`screenshot`/`cookies`/`network`
drive the actual page, not just the tab — useful for an agent that needs to
log a state, submit a form, or confirm a fix rendered. `open` brings the
agent browser to the front of your other windows the moment it starts,
because macOS stops rendering a window it can't see at all, and a page
rendered at zero size is what `screenshot` would otherwise return. If you
cover the agent browser with another window later, expect the same until you
bring it forward again.

`screenshot` captures only what is on screen, the same as a person looking at
the window — not the whole scrollable page. `click`/`fill`/`text` are real
WebDriver interactions (`element.click()`, `element.send_keys()`), not
scripted ones: a click sends a real, trusted click event and auto-scrolls
the target into view for you. `scroll` is still the only way to trigger
scroll-driven page behavior, like `IntersectionObserver` lazy-loading or
infinite-scroll feeds, since a click auto-scrolling to what it needs never
moves the viewport for anything else that happens to be watching scroll
position.

`click`'s target is a css selector by default, or exact viewport coordinates
as `x,y` — `zen-cli click 1 "400,300"` moves a real pointer there and
clicks, the same primitive `hover` and `key` use for pointer and keyboard
input. `key` takes a named key (`Enter`, `Escape`, `Tab`, `ArrowDown`, ...)
or a single literal character for anything not in that list. `screenshot`
takes an optional selector to capture just that element instead of the
whole screen.

`network` lists same-origin requests since the page loaded — url, type,
duration, and the real HTTP status, including failures like a 404. There is
no request interception, no headers or bodies: WebDriver classic (what Zen
speaks) has no CDP-style network domain, so this reads the page's own
`Resource Timing API` instead — a real browser capability, not a custom
mechanism. Cross-origin requests report as `cross-origin` rather than a
status, since `Timing-Allow-Origin` hides that detail from the page unless
the server opts in; that is a real web platform restriction, not a gap in
this tool.

A `fill` in one command and a `click` in the next stay on the same page: a
small background daemon (started on first use, alongside the browser) keeps
one Marionette connection alive across commands, because Firefox resets an
input's typed value the moment the connection watching its tab disconnects —
which every command used to do, before returning to the shell.

One known gap: clicking a link that navigates elsewhere is not reflected in
a later `list`/`close` by URL — Firefox does not reliably update a tab's
tracked location for a cross-origin navigation triggered from the page
itself, only chrome-driven ones. Targeting that tab by its `list` index still
works fine; it is only URL-based targeting that goes stale after a click.

## Teardown

```bash
cd "$worktree" && zen-cli destroy
```

Or let `gc` catch it later if the worktree is already gone.

## Why a second browser

Zen folders are browser UI, and only privileged code inside Zen can create
them. Reaching that code means enabling Marionette, which makes the browser
announce itself as automated — enough for Cloudflare and friends to block it.
Running that on your daily profile breaks the sites you actually use, so
zen-cli runs its own.

That profile starts empty. Your cookies and passwords are personal data, so
moving them into a second browser is something you ask for, not something a
tool does on your behalf while opening a tab.

## Requirements

Zen, and Python 3.11 or 3.12.

## License

MIT
