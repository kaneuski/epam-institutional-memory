# Onboarding KB Registers

A portable knowledge-base ontology for tracking institutional memory in a domain where most facts
**get superseded, not just accumulated** — org roles, service ownership, access policies. Built for
new-employee onboarding, modeled on the synthetic dataset at
[rosscrooke/institutional-memory](https://github.com/rosscrooke/institutional-memory).

These files are entirely self-contained — drop this whole folder into any project that needs the same
pattern.

---

## Why this exists

Most knowledge-base designs assume facts only accumulate (more pain points, more decisions, all still
true at once). This domain is different: at any moment, there's exactly **one** current Head of
Engineering, **one** current owner of `payment-service`, **one** active production-access policy. A
new document doesn't add a fact — it **retires an old one and replaces it**. The whole point of this
ontology and its tooling is making that retirement explicit and checkable, so a stale reference (a
handbook still citing last quarter's policy, a note still naming the previous Head of Engineering)
gets caught by a linter instead of misleading the next new hire.

See `kb-register-schema.md` for the full spec: all 12 registers, every field, every lint rule.

---

## Folder structure

```
onboarding-kb-registers/
├── README.md                   ← this file
├── kb-register-schema.md       ← the ontology spec (registers, fields, lint rules)
├── scaffold-registers.py       ← creates an empty .registers/ directory
├── tools/
│   ├── kb-lint.py              ← validates .registers/ against the schema
│   └── kb-browser.py           ← generates an interactive HTML browser
├── skills/
│   ├── kb-updater/SKILL.md     ← ingest a source doc into .registers/
│   ├── kb-snapshot/SKILL.md    ← write a current-state digest (read-only)
│   └── kb-browser/SKILL.md     ← generate + open the HTML browser (read-only)
└── data/
    ├── round1/                 ← baseline onboarding docs (handbook, policy, directory)
    └── round2/                 ← later updates to the same docs (policy rewrite, re-org)
```

`.registers/` itself isn't checked in here — it's generated. The leading dot is deliberate: it marks
generated, continuously-mutated state, not source code. Treat it like a `.cache/` directory.

---

## Quickstart: scaffold the registers

From wherever you want `.registers/` to live:

```bash
python3 scaffold-registers.py
```

This creates `.registers/` with all 12 empty register files (`policies.md`, `decisions.md`,
`role-assignments.md`, `service-ownership.md`, `incidents.md`, `people.md`, `teams.md`, `services.md`,
`access-tiers.md`, `onboarding-stages.md`, `exceptions.md`, `open-questions.md`), each with the
correct frontmatter (`type`, `tier`, `lifecycle`, `id_prefix`, `singleton_key`, `source_doc_types`).

Pass `--path` to target a different location, or `--dry-run` to preview without writing:

```bash
python3 scaffold-registers.py --path some/other/dir --dry-run
```

---

## Ingesting data

Ingestion is the `kb-updater` skill's job — it reads one source document and updates `.registers/`
accordingly. The `data/` folder has a worked example you can use to see the whole supersession story
play out:

1. **Ingest the round 1 baseline** — run `kb-updater` against each file in `data/round1/`:
   `onboarding-handbook.md`, `access-policy.md`, `team-directory.md`. This populates `.registers/`
   from scratch: `policies.md` gets the original access policy, `role-assignments.md` gets Anika Reddy
   as Head of Engineering, `service-ownership.md` gets Tom Bryce on `payment-service`, and so on.
2. **Ingest the round 2 updates** — run `kb-updater` against `data/round2/policy-update-2026-05-15.md`
   and `data/round2/team-directory-update.md`. This is where the supersede algorithm actually does
   something: the old access policy flips to `status: superseded` and a new `POL` entry takes over;
   Anika's role-assignment entry flips to `former` and Yuki Tanaka's new entry becomes `current`; the
   `payment-service` ownership entry flips similarly to Maya Patel.
3. **Lint** — `kb-updater` runs `tools/kb-lint.py` automatically at the end of ingestion, but you can
   run it any time:

   ```bash
   python3 tools/kb-lint.py --path .registers
   ```

   A clean ingestion of both rounds should lint clean. If you skip the supersede step and just append
   the round 2 facts as new entries without retiring the round 1 ones, the linter's singleton-violation
   check (#6) will catch it immediately — that's the scenario this whole ontology exists to prevent.

You don't have to use the sample data — any policy doc, team directory, or handbook revision works,
as long as it reads like one of those five files (a versioned policy, an org-change announcement, an
ownership table).

---

## The skills

Each skill does exactly one thing — there's no "modes" to choose between.

### `kb-updater` — ingest a source document

**Triggers:** "update the registers", "ingest this doc", "add this to the KB".

Reads one source document, classifies it, and either appends new entries (for non-singleton registers
like `decisions`, `incidents`, `open-questions`) or runs the **supersede algorithm** (for singleton
registers like `policies`, `role-assignments`, `service-ownership`, `access-tiers`): flip the old
current entry to `former`/`superseded`, link it to the new one in both directions, and propagate the
change to anything that pointed at the old entry (`access-tiers.governing_policy`,
`exceptions.modifies_policy`, `onboarding-stages.policy_ref`). Lints and fixes what it can before
reporting back. This is the only skill that writes to `.registers/`.

### `kb-snapshot` — read-only current-state digest

**Triggers:** "what's the current state", "who's the current owner of X", "give me the org chart now".

Walks every singleton and open-item register, collects only what's true *right now*, and writes a
dated `current-state-{YYYY-MM-DD}.md` with everything linked back to its source entry. Doesn't modify
anything — if lint finds issues while snapshotting, it points you at `kb-updater` rather than fixing
them itself.

### `kb-browser` — interactive HTML browser

**Triggers:** "show me the registers", "browse the KB", "open the graph".

Validates references first (surfacing singleton violations and stale pointers before you browse), then
generates a self-contained HTML file with two views:

- **Register list**, with a **timeline slider** running from the oldest dated entry to today. Drag it
  back and superseded policies, former role-holders, and prior service owners reappear exactly as they
  looked on that date — no need to manually walk `supersedes` chains.
- **Graph**, always showing the **current** relationship snapshot only — the slider is disabled there,
  since a relationship graph only ever needs to answer "how does this fit together right now."

Doesn't modify anything — broken references and singleton violations are surfaced for `kb-updater` to
fix, not repaired here.

---

## The tools (direct CLI use)

You don't need the skills to run these by hand:

```bash
# Validate .registers/ against the schema (11 checks: structural + domain-specific)
python3 tools/kb-lint.py --path .registers [--strict] [--json]

# Generate the HTML browser
python3 tools/kb-browser.py --path .registers --output kb-browser.html
```

`kb-lint.py` exits `0` clean, `2` warnings-only, `1` on errors (or on warnings with `--strict`) — wire
it into CI if `.registers/` is checked in anywhere.

---

## Further reading

`kb-register-schema.md` has the full spec: every register's exact fields, the singleton-key concept,
the traceability chain (`INC → DEC → POL → AT/EXC`, `DEC → POS/OWN`), and all 11 lint checks with the
reasoning behind each one.
