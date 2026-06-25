# Onboarding / Institutional-Memory KB Register Schema

Version: 1.0-draft
Source domain: new-employee onboarding & org institutional memory.

This spec is domain-portable: it is not tied to any specific engagement repo. Drop the files in this
folder into any project that needs to track onboarding docs, policies, org structure, and ownership
over time.

---

## 1. Design Principles

1. **Typed registers, not individual files**: one markdown file per entity type, all instances inside it.
2. **Entries are addressable by ID**: `{PREFIX}-{NNN}`, cross-referenced via `[ID](register-file.md#id)`.
3. **Frontmatter declares the register type, tier, and lifecycle.**
4. **Entries are delimited by `## {ID}: {Title}` headings.** `##` is reserved for entries only.
5. **Relationships are explicit markdown links**, with the field name carrying relationship semantics.
6. **Lifecycle states are first-class.** Evolving entities carry a `status` field with a defined state machine.
7. **Singleton-scoped registers are first-class.** Unlike a typical append-only knowledge base, where
   many entries (pain points, open questions, decisions) can be open at once, most core entities here
   represent **"the current truth" of something** — who holds a role, who owns a service, which policy
   version is in force — and at most one entry may hold `status: current` (or `active`) per logical key
   at any time. Each such register declares a
   `singleton_key` in its frontmatter. This is the property the linter exists to protect, because the
   dataset's core failure mode is a stale reference to a fact that has since been superseded (e.g. a
   note still citing the previous Head of Engineering, or a handbook still citing a retired policy).
8. **Stale-pointer integrity is checked, not just link integrity.** It is not enough for a link to
   resolve to *an* entry — `governing_policy`, `modifies_policy`, and `policy_ref` fields must resolve
   to entries that are still `status: active`. A link that resolves but points at a superseded entity
   is exactly the bug class this ontology is built to catch.

---

## 2. Physical Layout

```
.registers/
├── policies.md            # Core tier — singleton per scope
├── decisions.md           # Core tier
├── role-assignments.md    # Core tier — singleton per role_title
├── service-ownership.md   # Core tier — singleton per service
├── incidents.md           # Core tier
├── people.md              # Domain tier
├── teams.md                # Domain tier
├── services.md             # Domain tier
├── access-tiers.md         # Domain tier — singleton per tier_name
├── onboarding-stages.md    # Traceability tier
├── exceptions.md           # Traceability tier
└── open-questions.md       # Traceability tier
```

The leading dot is deliberate: `.registers/` holds generated, continuously-superseded state written by
`kb-updater`, not source code or static reference docs. Treat it the way you'd treat a `.cache/` or
`.terraform/` directory — something tooling reads and writes, not something a human hand-edits or
reviews line-by-line in a PR diff.

### Naming conventions
- Register filenames: lowercase, hyphenated plural noun matching the entity type.
- Entry IDs: `{PREFIX}-{NNN}`, zero-padded to 3 digits, sequential within a register, never reused.
- If an entry is superseded/closed, it keeps its ID with an updated `status` — IDs are never recycled.

---

## 3. Register File Format

```markdown
---
type: {entity-type-name}
tier: core | domain | traceability
lifecycle: evolving | static | tracked-until-closed
id_prefix: {PREFIX}
singleton_key: {field name} or null
source_doc_types: [doc-type-1, doc-type-2]
last_updated: {ISO-8601}
---

# {Register Title}

Brief description of what this register tracks.

---

## {ID}: {Entry Title}

| Field | Value |
|-------|-------|
| status | {lifecycle state} |
| ... | ... |

{Free-form body sections}

### References
- {Relationship label}: [ID](register.md#id)

---
```

### Field-table convention
Field-table cells hold **plain ID text** (e.g. `POL-002`), not markdown links. Markdown links live only
in the `### References` section. This keeps the field table machine-parseable (the linter reads it
directly) while the References section remains the human-navigable, clickable view. Both must agree —
if a field says `supersedes: POL-001`, the References section must contain
`- Supersedes: [POL-001](policies.md#pol-001)`.

### Evidence tags
A simple confidence convention — `[DIRECT]`, `[INFERRED]`, `[UNVERIFIED]` — applicable to any
body-text claim, especially in `decisions.md` and `incidents.md` where provenance matters.

---

## 4. ID Scheme Registry

| Prefix | Register | Tier | Lifecycle | Singleton key |
|--------|----------|------|-----------|---------------|
| POL | policies.md | core | evolving | `scope` (among `status: active`) |
| DEC | decisions.md | core | evolving | — |
| POS | role-assignments.md | core | evolving | `role_title` (among `status: current`) |
| OWN | service-ownership.md | core | evolving | `service` (among `status: current`) |
| INC | incidents.md | core | tracked-until-closed | — |
| PER | people.md | domain | static | — |
| TEAM | teams.md | domain | static | — |
| SYS | services.md | domain | static | — |
| AT | access-tiers.md | domain | evolving | `tier_name` (always unique) |
| STAGE | onboarding-stages.md | traceability | static | — |
| EXC | exceptions.md | traceability | tracked-until-closed | — |
| OQ | open-questions.md | traceability | tracked-until-closed | — |

All prefixes are globally unique across registers to prevent collision.

---

## 5. Register Definitions

### 5.1 Core Tier

#### 5.1.1 Policies (`policies.md`)

```yaml
---
type: policy
tier: core
lifecycle: evolving
id_prefix: POL
singleton_key: scope
source_doc_types: [policy-doc]
last_updated: 2026-06-24
---
```

```markdown
## POL-{NNN}: {Policy Name}

| Field | Value |
|-------|-------|
| status | active \| superseded |
| scope | {what this governs, e.g. "prod-access"} |
| effective_date | {YYYY-MM-DD} |
| superseded_date | {YYYY-MM-DD or null} |
| owner | {PER-NNN, ...} |
| supersedes | {POL-NNN or null} |
| superseded_by | {POL-NNN or null} |
| source_incident | {INC-NNN or null} |
| migration_deadline | {YYYY-MM-DD or null} |

**What it governs:** {one-line scope statement}

**Statement:** {the rules themselves}

**What changed and why:** {only present on a superseding version}

**Review cadence:** {how often this is revisited, by whom}

### References
- Supersedes: [POL-{NNN}](policies.md#pol-nnn)
- Superseded by: [POL-{NNN}](policies.md#pol-nnn)
- Triggered by: [INC-{NNN}](incidents.md#inc-nnn)
- Decision: [DEC-{NNN}](decisions.md#dec-nnn)
- Owner: [PER-{NNN}](people.md#per-nnn)
- Governs: [AT-{NNN}](access-tiers.md#at-nnn), [EXC-{NNN}](exceptions.md#exc-nnn)
```

**State machine:** `active → superseded` (terminal; never deleted). **Singleton rule:** at most one
`status: active` entry per `scope` value.

---

#### 5.1.2 Decisions (`decisions.md`)

```yaml
---
type: decision
tier: core
lifecycle: evolving
id_prefix: DEC
singleton_key: null
source_doc_types: [policy-doc, team-directory-update]
last_updated: 2026-06-24
---
```

```markdown
## DEC-{NNN}: {Decision Title}

| Field | Value |
|-------|-------|
| status | active \| reversed |
| decision_type | policy \| org-change \| ownership-change \| process |
| date | {YYYY-MM-DD} |
| participants | {PER-NNN, ...} |
| trigger | {INC-NNN or null} |
| reversibility | irreversible \| costly-to-reverse \| easily-reversed |

**Decision:** {clear statement of what was decided}

**Rationale:** {why this was chosen}

**Alternatives eliminated:** {what was rejected and why}

**Consequences:** {what this enables or constrains}

### References
- Triggered by: [INC-{NNN}](incidents.md#inc-nnn)
- Produces: [POL-{NNN}](policies.md#pol-nnn), [POS-{NNN}](role-assignments.md#pos-nnn), [OWN-{NNN}](service-ownership.md#own-nnn), [EXC-{NNN}](exceptions.md#exc-nnn)
- Participants: [PER-{NNN}](people.md#per-nnn)
```

**State machine:** `active → reversed`. A decision should always have at least one `Produces` link —
the linter warns on orphaned decisions (recorded but never applied to a register).

---

#### 5.1.3 Role Assignments (`role-assignments.md`)

```yaml
---
type: role-assignment
tier: core
lifecycle: evolving
id_prefix: POS
singleton_key: role_title
source_doc_types: [team-directory, team-directory-update]
last_updated: 2026-06-24
---
```

```markdown
## POS-{NNN}: {Person} — {Role Title}

| Field | Value |
|-------|-------|
| status | current \| former |
| person | {PER-NNN} |
| role_title | {e.g. "Head of Engineering"} |
| team | {TEAM-NNN or null} |
| start_date | {YYYY-MM-DD} |
| end_date | {YYYY-MM-DD or null} |
| supersedes | {POS-NNN or null} |
| superseded_by | {POS-NNN or null} |
| decision | {DEC-NNN or null} |

**Responsibilities:** {what this role owns}

**Notes:** {free text}

### References
- Person: [PER-{NNN}](people.md#per-nnn)
- Team: [TEAM-{NNN}](teams.md#team-nnn)
- Supersedes: [POS-{NNN}](role-assignments.md#pos-nnn)
- Superseded by: [POS-{NNN}](role-assignments.md#pos-nnn)
- Decision: [DEC-{NNN}](decisions.md#dec-nnn)
```

**State machine:** `current → former`, flipped when a new POS entry for the same `role_title` is
created. **Singleton rule:** at most one `status: current` entry per `role_title`.

---

#### 5.1.4 Service Ownership (`service-ownership.md`)

```yaml
---
type: service-ownership
tier: core
lifecycle: evolving
id_prefix: OWN
singleton_key: service
source_doc_types: [onboarding-handbook, team-directory-update]
last_updated: 2026-06-24
---
```

```markdown
## OWN-{NNN}: {Service Name} Ownership

| Field | Value |
|-------|-------|
| status | current \| former |
| service | {SYS-NNN} |
| owning_team | {TEAM-NNN} |
| tech_lead | {PER-NNN} |
| start_date | {YYYY-MM-DD} |
| end_date | {YYYY-MM-DD or null} |
| supersedes | {OWN-NNN or null} |
| decision | {DEC-NNN or null} |

**Notes:** {free text}

### References
- Service: [SYS-{NNN}](services.md#sys-nnn)
- Team: [TEAM-{NNN}](teams.md#team-nnn)
- Tech lead: [PER-{NNN}](people.md#per-nnn)
- Supersedes: [OWN-{NNN}](service-ownership.md#own-nnn)
- Decision: [DEC-{NNN}](decisions.md#dec-nnn)
```

**Singleton rule:** at most one `status: current` entry per `service`.

---

#### 5.1.5 Incidents (`incidents.md`)

```yaml
---
type: incident
tier: core
lifecycle: tracked-until-closed
id_prefix: INC
singleton_key: null
source_doc_types: [policy-doc]
last_updated: 2026-06-24
---
```

```markdown
## INC-{NNN}: {Incident Title}

| Field | Value |
|-------|-------|
| status | open \| investigating \| resolved |
| severity | P0 \| P1 \| P2 |
| date | {YYYY-MM-DD} |
| postmortem_link | {URL or null} |

**Summary:** {what happened}

**Impact:** {who/what was affected}

**Root cause:** {if known}

### References
- Drove: [DEC-{NNN}](decisions.md#dec-nnn)
- Related policy: [POL-{NNN}](policies.md#pol-nnn)
```

**State machine:** `open → investigating → resolved`. **Lint rule:** `status: resolved` with
`severity` in `{P0, P1}` requires a non-null `postmortem_link`.

---

### 5.2 Domain Tier

#### 5.2.1 People (`people.md`)

```yaml
---
type: person
tier: domain
lifecycle: static
id_prefix: PER
singleton_key: null
source_doc_types: [team-directory, team-directory-update]
last_updated: 2026-06-24
---
```

```markdown
## PER-{NNN}: {Name}

| Field | Value |
|-------|-------|
| status | active \| on-leave \| departed |
| join_date | {YYYY-MM-DD} |
| location | {city} |
| slack_handle | {@handle} |

**Notes:** {free text, e.g. tenure-specific institutional knowledge}

### References
- Current role: *(derived — look up the `status: current` entry in role-assignments.md where `person` = this ID; not stored here, so it cannot go stale independently)*
```

Current title is intentionally **not** a stored field on `people.md` — it is always derived from
`role-assignments.md`. Storing it twice would create a second place that can drift out of sync, which
is precisely the bug this ontology exists to prevent.

---

#### 5.2.2 Teams (`teams.md`)

```yaml
---
type: team
tier: domain
lifecycle: static
id_prefix: TEAM
singleton_key: null
source_doc_types: [team-directory]
last_updated: 2026-06-24
---
```

```markdown
## TEAM-{NNN}: {Team Name}

| Field | Value |
|-------|-------|
| parent_team | {TEAM-NNN or null} |

**Mission:** {what this team is responsible for}

### References
- Lead: [POS-{NNN}](role-assignments.md#pos-nnn) *(must be `status: current`)*
- Members: [PER-{NNN}](people.md#per-nnn), ...
- Owns services: [OWN-{NNN}](service-ownership.md#own-nnn), ... *(must be `status: current`)*
```

---

#### 5.2.3 Services (`services.md`)

```yaml
---
type: service
tier: domain
lifecycle: static
id_prefix: SYS
singleton_key: null
source_doc_types: [onboarding-handbook]
last_updated: 2026-06-24
---
```

```markdown
## SYS-{NNN}: {Service Name}

| Field | Value |
|-------|-------|
| repo_link | {URL or null} |

**Description:** {what this service does}

### References
- Current ownership: [OWN-{NNN}](service-ownership.md#own-nnn)
- Ownership history: [OWN-{NNN}](service-ownership.md#own-nnn), ...
```

---

#### 5.2.4 Access Tiers (`access-tiers.md`)

```yaml
---
type: access-tier
tier: domain
lifecycle: evolving
id_prefix: AT
singleton_key: tier_name
source_doc_types: [policy-doc, onboarding-handbook]
last_updated: 2026-06-24
---
```

```markdown
## AT-{NNN}: {Tier Name}

| Field | Value |
|-------|-------|
| tier_name | read-only \| read-write \| privileged |
| governing_policy | {POL-NNN} |

**Current eligibility:** {summary of current criteria — restated whenever governing_policy changes}

**Use cases:** {what this tier is for}

### References
- Governing policy: [POL-{NNN}](policies.md#pol-nnn) *(must be `status: active`)*
- Exceptions: [EXC-{NNN}](exceptions.md#exc-nnn), ...
```

**Singleton rule:** exactly one AT entry per `tier_name` (no duplicates, regardless of status — there
is one row per tier, its `governing_policy` field is updated in place when policy changes — see
migration note in §7).

---

### 5.3 Traceability Tier

#### 5.3.1 Onboarding Stages (`onboarding-stages.md`)

```yaml
---
type: onboarding-stage
tier: traceability
lifecycle: static
id_prefix: STAGE
singleton_key: null
source_doc_types: [onboarding-handbook]
last_updated: 2026-06-24
---
```

```markdown
## STAGE-{NNN}: {Stage Name}

| Field | Value |
|-------|-------|
| sequence_order | {1-based} |
| day_range | {e.g. "Day 1", "Day 2-5"} |
| handbook_version | {version this stage came from} |
| policy_ref | {POL-NNN or null} |
| access_tier_ref | {AT-NNN or null} |

**Activities:** {what happens during this stage}

**Equipment/accounts granted:** {if applicable}

### References
- Mentor/buddy role: [TEAM-{NNN}](teams.md#team-nnn) or [PER-{NNN}](people.md#per-nnn)
- Access tier referenced: [AT-{NNN}](access-tiers.md#at-nnn)
- Policy referenced: [POL-{NNN}](policies.md#pol-nnn) *(must be `status: active`, else the handbook content is stale)*
```

---

#### 5.3.2 Exceptions (`exceptions.md`)

```yaml
---
type: exception
tier: traceability
lifecycle: tracked-until-closed
id_prefix: EXC
singleton_key: null
source_doc_types: [policy-doc]
last_updated: 2026-06-24
---
```

```markdown
## EXC-{NNN}: {Exception Name}

| Field | Value |
|-------|-------|
| status | active \| superseded \| revoked |
| modifies_policy | {POL-NNN} |
| trigger_condition | {what condition activates this exception} |
| reconciliation_deadline | {e.g. "within 5 working days" or YYYY-MM-DD, or null} |

**Override behavior:** {what's different from the standard policy}

**Reconciliation requirement:** {what must happen afterward, and what happens if it doesn't}

### References
- Modifies: [POL-{NNN}](policies.md#pol-nnn) *(must be `status: active`)*
```

---

#### 5.3.3 Open Questions (`open-questions.md`)

```yaml
---
type: open-question
tier: traceability
lifecycle: tracked-until-closed
id_prefix: OQ
singleton_key: null
source_doc_types: [any]
last_updated: 2026-06-24
---
```

```markdown
## OQ-{NNN}: {Question Summary}

| Field | Value |
|-------|-------|
| status | open \| answered \| deferred |
| raised_date | {YYYY-MM-DD} |
| priority | blocking \| important \| nice-to-know |
| source | {doc or register entry that raised this} |

**Question:** {full text}

**Context:** {why this matters}

**Resolution:** {answer when resolved, or null}

### References
- Related to: [ID](register-file.md#id)
```

---

## 6. Cross-Reference Conventions

| Field name | Meaning |
|---|---|
| `Source` | Provenance — where this entity was first identified |
| `Supersedes` / `Superseded by` | Same logical entity, newer/older version — bidirectional |
| `Triggered by` | Upstream incident that caused a decision |
| `Produces` | Downstream artifacts a decision created or changed |
| `Modifies` | An exception's relationship to the policy it overrides |
| `Governs` | A policy's relationship to the access tiers / exceptions it controls |
| `Decision` | The decision that authorized this change |
| `Related to` | Loose association, no dependency |

### Traceability chain

```
INC-NNN → DEC-NNN → POL-NNN ─┬→ AT-NNN   ← STAGE-NNN (cites)
                              └→ EXC-NNN
                DEC-NNN → POS-NNN  ← STAGE-NNN (buddy/lead lookups)
                DEC-NNN → OWN-NNN  ← TEAM-NNN / SYS-NNN
```

---

## 7. Lifecycle & State Machines

| Register | States | Terminal |
|---|---|---|
| policies | active → superseded | superseded |
| decisions | active → reversed | reversed |
| role-assignments | current → former | former |
| service-ownership | current → former | former |
| incidents | open → investigating → resolved | resolved |
| exceptions | active → superseded \| revoked | superseded, revoked |
| open-questions | open → answered \| deferred | answered |

Domain-tier entities (`people`, `teams`, `services`) are `static` — created once, mutated only on
correction. `access-tiers` is the one domain-tier exception: it is `evolving` because its
`governing_policy` pointer and `current_eligibility` text are expected to change every time the
policy they describe is superseded — that update is what keeps AT entries from becoming the stale
pointer described in §8 rule 7 below.

---

## 8. Lint Rules

**Generic (structural integrity checks any markdown-register KB needs):**

1. Every markdown link resolves to an existing entry in some register.
2. ID prefixes match their declared register file.
3. No duplicate IDs within a register.
4. Bidirectional references are present for `Supersedes`/`Superseded by` and `Modifies` pairs (warns on one-way links).
5. `status` values are members of the register's allowed lifecycle states.

**Domain-specific (the reason this ontology exists):**

6. **Singleton-current violation (error).** More than one entry shares a register's `singleton_key`
   value while both carry the "current" status (`active` for policies, `current` for role-assignments
   / service-ownership, always for access-tiers). This is the check that catches an unresolved org
   change — e.g. two `role-assignments` entries both `status: current` for `role_title: "Head of
   Engineering"`.
7. **Stale pointer to superseded policy (error).** `access-tiers.governing_policy`,
   `exceptions.modifies_policy`, or `onboarding-stages.policy_ref` resolves to a `policies.md` entry
   whose `status` is `superseded`. This is the same bug class as rule 6, but for policy-derived facts
   instead of people facts — it catches a handbook or access tier that still points at last quarter's
   policy.
8. **Date ordering (error).** A superseding entry's `effective_date`/`start_date` must be on or after
   the `effective_date`/`start_date` of the entry named in its `supersedes` field.
9. **Orphaned decision (warning).** A `decisions.md` entry has no `Produces` link to any
   `policies` / `role-assignments` / `service-ownership` / `exceptions` entry — the decision was
   recorded but never reflected in the registers it should have changed.
10. **Incident-postmortem completeness (error).** An `incidents.md` entry with `severity` in
    `{P0, P1}` and `status: resolved` has an empty `postmortem_link`.
11. **Migration deadline drift (warning).** A `policies.md` entry's `migration_deadline` has passed
    (relative to today) — flagged for manual review of whether dependents were reconciled.

---

## 9. Tooling

- `scaffold-registers.py` (repo root) — creates the 12 empty register files with correct frontmatter
  for a new project.
- `tools/kb-lint.py` — implements all eleven checks in §8. Run via
  `python3 tools/kb-lint.py --path <registers dir>`.
- `tools/kb-browser.py` — generates the HTML register browser with the timeline slider (see
  `skills/kb-browser/SKILL.md`).
