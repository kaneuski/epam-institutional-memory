---
name: kb-browser
description: Generate and open an interactive HTML browser for the onboarding/institutional-memory KB registers, with a timeline slider to see how any register looked as of a past date. Runs reference validation first and surfaces any broken links before opening the browser.
---

# kb-browser — Onboarding KB Register Browser

Validates cross-reference integrity in the registers, then generates a self-contained HTML browser.
Read-only — never writes to registers.

There is no "all registers" view — the sidebar tree (Core / Domain / Traceability) requires picking a
specific register before any entries render, since showing all 12 registers' entries at once is too
much to scan. On open, the content area shows a placeholder prompting that choice.

The browser has two distinct views, deliberately treated differently:

- **Register list view** — has a **timeline slider** running from the oldest dated entry to today, but
  only for the registers it applies to (Core, plus People and Open Questions — see "How the timeline
  slider works" below). Moving it filters those registers down to what was true as of that date:
  superseded policies, former role holders, and prior service owners reappear as you slide back, and
  entries that didn't exist yet disappear. For every other register, and while the Graph view is active,
  the timeline bar is hidden entirely rather than shown disabled — there's nothing for it to filter, so
  there's nothing to show.
- **Graph view** — always shows the **current** relationship snapshot only, with `+`/`−`/Reset zoom
  controls in its toolbar for navigating dense graphs. The timeline slider is hidden while this view is
  active — a relationship graph answers "how does this fit together right now," not "how did this look
  in the past," so there's nothing to slide.

---

## Before you start

Check that `.registers/` exists.

```
ls .registers/
```

- **Directory does not exist:** Tell the user: "No registers found. Run `python3
  scaffold-registers.py --path .registers` first, or run `kb-updater` to populate it from a source
  document." Stop.
- **Directory is empty:** Tell the user: "The registers directory exists but contains no entries yet.
  Ingest a source document with `kb-updater` first, then come back." Stop.

---

## Step 1: Validate cross-reference integrity

```
python3 tools/kb-lint.py --path .registers --json
```

Parse the JSON output — check `errors` and `warnings` counts.

**Exit code 0 — no issues:** Proceed silently to Step 2.

**Exit code 2 — warnings only:** Show a summary of warnings, then proceed to Step 2.

**Exit code 1 — errors found (including singleton violations or stale policy pointers):** Surface the
errors:

> ⚠️ **Found N issues, including {singleton violations / stale pointers if present}.**
> [paste lint output here]
> Consider running `kb-updater` to fix these before browsing — a singleton violation or stale pointer
> means the timeline slider will show two "current" answers for the same question at once.

Then ask the user whether to continue:

> **How would you like to proceed?**
> 1. Open browser anyway
> 2. Cancel

If the user cancels, stop here.

---

## Step 2: Generate the HTML browser

```
python3 tools/kb-browser.py --path .registers --output kb-browser-[YYYY-MM-DD-HHMMSS].html
```

The graph is generated unconditionally every time — there's no flag for it, since there's no
timeline-affected variant to choose between.

If the command fails, surface the error output and stop.

---

## Step 3: Open in browser

```
open kb-browser-[YYYY-MM-DD-HHMMSS].html 2>/dev/null || xdg-open kb-browser-[YYYY-MM-DD-HHMMSS].html 2>/dev/null || start kb-browser-[YYYY-MM-DD-HHMMSS].html 2>/dev/null || echo "OPEN_FAILED"
```

- If the command succeeds (no `OPEN_FAILED`), tell the user: "KB browser opened — saved to
  `kb-browser-[date-time].html`. Drag the slider at the top to see how the registers looked on any past
  date; switch to the Graph item in the sidebar for the current relationship map."
- If `OPEN_FAILED`, tell the user: "Generated `kb-browser-[date-time].html` — could not open
  automatically. Open it manually in your browser."

Use a timestamp down to the second (e.g. `2026-06-24-153045`), not just the date — this skill can run
several times in one day while iterating on registers, and a date-only filename would silently
overwrite the previous run's snapshot instead of leaving a trail of them.

---

## How the timeline slider works (for reference, if asked)

The slider only filters a fixed set of registers — the Core tier (`policies`, `decisions`,
`role-assignments`, `service-ownership`, `incidents`) plus `people` and `open-questions`. This is a
deliberate allow-list, not an inference from which fields happen to be present: `teams`, `services`,
`access-tiers`, `onboarding-stages`, and `exceptions` are excluded outright, even though some of them
(`access-tiers` in particular) do change over time in practice — their eligibility/governing-policy
pointer evolves, but the register itself carries no date field to anchor that on a timeline, so it's
treated as a static, always-shown record rather than a half-correct one.

When browsing a register the slider doesn't apply to, the timeline bar is hidden outright rather than
shown greyed-out — same treatment as the Graph view, which hides it for a different reason (it only ever
shows the current snapshot).

For the registers the slider *does* apply to, each entry's valid time window is derived from its own
fields, in priority order:

- **Start:** `start_date` → `effective_date` → `date` → `raised_date` → `join_date` (first one present).
- **End:** `end_date` → `superseded_date` (first one present).

An entry with a start but no end is shown from that date onward, indefinitely (e.g. an open incident, an
unresolved open question, the current holder of a role). An entry with both a start and an end is shown
only inside that window — sliding past the end date makes it disappear and reveals whatever superseded
it, which is exactly the failure mode this ontology exists to make visible: at any point on the
timeline, the slider can answer "who was the Head of Engineering then?" or "which policy governed
access then?" without needing to manually walk `supersedes` chains.

The slider's tick marks are every distinct start date found across the timeline-eligible registers, plus
today. There is a **Now** button that jumps straight back to the rightmost (current) position.

---

## What this skill does not do

- It does not modify any register files.
- It does not repair broken references, singleton violations, or stale pointers — use `kb-updater` for
  that.
- It does not push or publish the HTML file anywhere — share it manually if needed.
