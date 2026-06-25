---
name: kb-updater
description: Use this skill to ingest a new onboarding/institutional-memory source document (policy update, team directory update, handbook revision, incident postmortem) into the registers defined in kb-register-schema.md. Triggers on "update the registers", "ingest this doc", "add this to the KB". For a point-in-time digest of current truth across all registers, use the kb-snapshot skill instead.
---

# KB Updater (Onboarding / Institutional-Memory Registers)

Keeps the 12 registers defined in `kb-register-schema.md` current and internally consistent as new
source documents arrive. The defining property of this domain — unlike a typical append-only
knowledge base — is that most core entities are **singleton-scoped**: a new document doesn't just add
a fact, it usually **retires an old one**. This skill's main job is performing that retirement
correctly (flip the old entry, link it to the new one, propagate the change to anything that pointed
at the old entry) so the linter never has to catch it after the fact.

For producing a human-readable digest of current truth across all registers, see the separate
`kb-snapshot` skill — that's a read-only reporting operation, not an ingestion one, so it doesn't live
here.

---

## Before you start

Check that a `.registers/` directory exists with the 12 files from `kb-register-schema.md`. If not,
stop and tell the user:

> "Registers directory not found. Run `python3 scaffold-registers.py --path .registers` to create it."

> **Single-writer rule:** only this skill writes to `.registers/`. This prevents ID collisions and
> keeps supersession chains consistent. The leading dot marks it as generated state, not source —
> don't hand-edit it outside this skill.

---

## Step 1: Classify the source document

Identify the document's type — `policy-doc`, `team-directory`, `team-directory-update`,
`onboarding-handbook`, `incident-postmortem`, or similar. Check each register's `source_doc_types`
frontmatter field to know which registers this document type can plausibly produce entries for. Skip
registers the document type doesn't touch.

## Step 2: For each candidate register, decide append vs. supersede

**Non-singleton registers** (`decisions`, `incidents`, `onboarding-stages`, `exceptions`,
`open-questions`) are append-only, same as a standard KB: new entity → new entry, next sequential ID.
Never modify existing entries in these registers.

**Singleton registers** (`policies`, `role-assignments`, `service-ownership`, `access-tiers`) require
the **supersede algorithm** instead of a plain append, whenever the document states or implies a
change to the current holder of a `singleton_key` value:

1. Find the existing entry in that register with `status: current` (or `active`) for the same
   `singleton_key` value (`scope` for policies, `role_title` for role-assignments, `service` for
   service-ownership, `tier_name` for access-tiers — note access-tiers has no status field; "supersede"
   for it means updating `governing_policy` and `current_eligibility` in place on the single existing
   entry, not creating a new one).
2. Flip that entry's `status` to `former`/`superseded`, set its `end_date`/`superseded_date` to the new
   entry's `start_date`/`effective_date`, and set its `superseded_by` field to the new entry's ID
   (assign the new ID first if needed).
3. Create the new entry with `status: current`/`active`, and set its `supersedes` field to the old
   entry's ID.
4. Add the reverse link too — `Supersedes`/`Superseded by` must appear in **both** entries' `###
   References` sections. Do this immediately; don't leave it for the linter's bidirectional-link
   warning to catch.

**Domain-tier identity registers** (`people`, `teams`, `services`) hold facts that don't get
superseded, only corrected. If the document introduces a new person/team/service not yet in the
register, create a stub entry. If it corrects a static fact about an existing one (e.g. a location
change), edit that field in place — these are not append-only.

**Extraction cues** — common phrasings and what they map to:

| Document phrasing | Action |
|---|---|
| "Effective {date}. Supersedes the {prior} version." | New `policies.md` entry, supersede the active POL for that `scope` |
| "{Name} has moved into a new role as {title}, effective {date}" | New `role-assignments.md` entry, supersede the current POS for that `role_title` |
| A "Was / Is now" ownership table | New `service-ownership.md` entry per row, supersede the current OWN for that `service` |
| "Following the {incident} review..." / an incident ID like `PROD-INC-NN-YYYY` | New (or existing) `incidents.md` entry, linked via `Triggered by` to a new `decisions.md` entry |
| "If you have notes referencing {old fact}, those are out of date" | Confirms a supersession already in progress — make sure the corresponding old entry's `status` is flipped, don't create a duplicate |
| "No longer required" / "eliminates the {step}" | Update the relevant `access-tiers.md` entry's `current_eligibility` text and re-point `governing_policy` |

## Step 3: Propagate stale pointers

After superseding a `policies.md` entry, find every entry elsewhere that points at the **old** POL ID
via a stale-pointer field — `access-tiers.governing_policy`, `exceptions.modifies_policy`,
`onboarding-stages.policy_ref` — and update it to the new POL ID, *provided the new policy actually
covers the same ground*. If the new policy doesn't cleanly cover what the old pointer referenced (e.g.
it only partially replaces the old policy), don't guess — surface it:

> "{AT-NNN/EXC-NNN/STAGE-NNN} points at {old POL-NNN}, now superseded by {new POL-NNN}. Re-point it, or
> does this entry need its own review? (Recommended: re-point)"

**Special case — exception whose trigger condition was eliminated, not just changed.** If an
`exceptions.md` entry's `trigger_condition`/`override_behavior` waives a specific step (e.g. "skip the
SRE pairing session") and the new policy removes that step from the process entirely rather than
changing its terms, don't re-point and don't ask — the exception has no condition left to modify.
Resolve it deterministically: flip the entry's `status` to `superseded`, set `superseded_date` to the
new policy's `effective_date`, and add a one-line note naming the eliminated step. This is distinct
from the general ambiguous case above (which still warrants asking) because there's nothing left to
decide — the override target is gone, not just relocated.

This step is what keeps the linter's stale-pointer check (#7) from ever firing — it exists precisely
because this is the bug class this ontology is designed to catch, so don't leave it for the linter to
report after the fact.

## Step 4: Record the decision and/or incident

If the document states a reason for a change ("Following the April incident review...", "we are
tightening...because..."), create a `decisions.md` entry capturing the rationale, and link it:

- `Triggered by` → the `incidents.md` entry, if one is named or implied.
- `Produces` → every `policies`/`role-assignments`/`service-ownership`/`exceptions` entry this decision
  caused. A decision with no `Produces` link is a lint warning (#9) — don't leave one dangling.
- Set the produced entries' `decision` field back to this DEC ID.

## Step 5: Lint and fix

```
python3 tools/kb-lint.py --path .registers --json
```

Auto-fix what's safe: missing back-links (additive), anchor mismatches. Surface anything else —
singleton violations, stale pointers that weren't resolved in Step 3, broken references — to the user
rather than guessing which entry is correct.

Re-run lint after fixes.

## Step 6: Report

> "Registers updated from {doc name}. {N} new entries, {M} superseded: {e.g. POL-002 (supersedes
> POL-001), POS-003 (supersedes POS-001)}. Lint: {N} issues fixed, {R} remaining."
