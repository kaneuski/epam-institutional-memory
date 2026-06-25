---
name: kb-snapshot
description: Use this skill to produce a human-readable digest of current truth across the onboarding/institutional-memory registers (active policies, current role holders, current service ownership, open items). Read-only — never writes to registers. Triggers on "what's the current state", "consolidate the registers", "who's the current owner of X", "give me the org chart now".
---

# KB Snapshot (Onboarding / Institutional-Memory Registers)

Produces a point-in-time digest of "what's true right now" across all 12 registers defined in
`kb-register-schema.md`. This is a read-only reporting operation — it never modifies a register. To
ingest a new source document and update the registers, use the separate `kb-updater` skill instead.

This skill exists because most of this domain's core registers are singleton-scoped (one current
policy per scope, one current holder per role, one current owner per service), which means the answer
to "what's true now" is scattered across many small entries connected by `supersedes` chains. A
snapshot collapses that into one document someone can read cold.

---

## Before you start

Check that a `.registers/` directory exists with the 12 files from `kb-register-schema.md`. If not,
stop and tell the user:

> "Registers directory not found. Run `python3 scaffold-registers.py --path .registers` to create it,
> then ingest a source document with `kb-updater` before snapshotting."

If it exists but every register is empty, tell the user there's nothing to snapshot yet and stop.

---

## Step 1: Identify scope

Ask if unclear: "Snapshot everything, or a specific register/scope (e.g. just service ownership, just
prod-access policy)?"

## Step 2: Walk every singleton and tracked-until-closed register, current entries only

For each register, collect only the entries that represent current truth:
- `policies`: `status: active`
- `role-assignments`: `status: current`
- `service-ownership`: `status: current`
- `access-tiers`: all entries (always current by definition)
- `incidents`, `exceptions`, `open-questions`: `status` not in a terminal state
- `decisions`: most recent N, or those linked from the above

## Step 3: Write the snapshot

Write `current-state-{YYYY-MM-DD}.md`:

```markdown
---
snapshot_date: [YYYY-MM-DD]
sources: [list of register files this summarizes]
---

# Current State — [YYYY-MM-DD]

## Active policies
[POL-NNN](.registers/policies.md#pol-nnn): {title} — effective {date}

## Current role holders
[POS-NNN](.registers/role-assignments.md#pos-nnn): {person} — {role_title}

## Current service ownership
[OWN-NNN](.registers/service-ownership.md#own-nnn): {service} — owned by {team}, led by {person}

## Access tiers
[AT-NNN](.registers/access-tiers.md#at-nnn): {tier_name} — governed by [POL-NNN]

## Open items
[OQ-NNN](.registers/open-questions.md#oq-nnn), [EXC-NNN](.registers/exceptions.md#exc-nnn), [INC-NNN](.registers/incidents.md#inc-nnn) not yet resolved
```

Reference register IDs inline everywhere — this snapshot is meant to answer "is this still true?" at a
glance, so every claim needs to be one click from its source entry.

## Step 4: Lint and confirm

Run `python3 tools/kb-lint.py --path .registers` once more — a snapshot is a good moment to catch drift
that accumulated across several ingests (singleton violations, stale pointers). Report:

> "Snapshot written: `current-state-{date}.md`. {N} active policies, {M} current role holders, {K}
> current ownerships, {J} open items. Lint: {N} issues, {R} remaining."

If lint found issues, point the user at `kb-updater` to fix them — this skill doesn't repair anything.

---

## What this skill does not do

- It does not modify any register files.
- It does not repair broken references, singleton violations, or stale pointers — use `kb-updater` for
  that.
- It does not ingest source documents — that's `kb-updater`'s job.
