---
type: role-assignment
tier: core
lifecycle: evolving
id_prefix: POS
singleton_key: "role_title"
source_doc_types: ["team-directory", "team-directory-update"]
last_updated: 2026-06-24
---

# Role Assignments

Who holds what role, with supersession history. At most one status:current entry per role_title.

---

## POS-001: Anika Reddy — Head of Engineering

| Field | Value |
|-------|-------|
| status | former |
| person | PER-002 |
| role_title | Head of Engineering |
| team | null |
| start_date | 2023-01-01 |
| end_date | 2026-04-15 |
| supersedes | null |
| superseded_by | POS-007 |
| decision | null |

**Responsibilities:** [INFERRED] Engineering leadership for BTS-Synthetic.

**Notes:** [DIRECT] team-directory.md, Jan 2026. `start_date` inferred from join date — no separate role-start date given. `end_date` set to the start date of [POS-007](role-assignments.md#pos-007) (Yuki's appointment), per the supersede algorithm; team-directory-update.md actually states Anika left this role on 2026-04-01, two weeks before Yuki started — a brief gap not separately modeled here.

### References
- Person: [PER-002](people.md#per-002)
- Superseded by: [POS-007](role-assignments.md#pos-007)

---

## POS-002: Carlos Mendes — Head of SRE

| Field | Value |
|-------|-------|
| status | current |
| person | PER-003 |
| role_title | Head of SRE |
| team | TEAM-001 |
| start_date | 2024-01-01 |
| end_date | null |
| supersedes | null |
| superseded_by | null |
| decision | null |

**Responsibilities:** Owns the on-call rotation.

**Notes:** [DIRECT] team-directory.md, Jan 2026.

### References
- Person: [PER-003](people.md#per-003)
- Team: [TEAM-001](teams.md#team-001)

---

## POS-003: Yuki Tanaka — Head of Platform

| Field | Value |
|-------|-------|
| status | former |
| person | PER-004 |
| role_title | Head of Platform |
| team | TEAM-002 |
| start_date | 2022-01-01 |
| end_date | 2026-04-15 |
| supersedes | null |
| superseded_by | POS-008 |
| decision | null |

**Responsibilities:** Owns auth, signing, and tenant-config services.

**Notes:** [DIRECT] team-directory.md, Jan 2026. Superseded as part of the May 2026 leadership re-org — Yuki moved up to Head of Engineering (see [POS-007](role-assignments.md#pos-007)).

### References
- Person: [PER-004](people.md#per-004)
- Team: [TEAM-002](teams.md#team-002)
- Superseded by: [POS-008](role-assignments.md#pos-008)

---

## POS-004: Maya Singh — Head of Security

| Field | Value |
|-------|-------|
| status | current |
| person | PER-001 |
| role_title | Head of Security |
| team | null |
| start_date | 2024-01-01 |
| end_date | null |
| supersedes | null |
| superseded_by | null |
| decision | null |

**Responsibilities:** Owns [POL-001](policies.md#pol-001), the production access policy.

**Notes:** [DIRECT] team-directory.md, Jan 2026.

### References
- Person: [PER-001](people.md#per-001)

---

## POS-005: Tom Bryce — Engineering Ops Lead

| Field | Value |
|-------|-------|
| status | former |
| person | PER-005 |
| role_title | Engineering Ops Lead |
| team | null |
| start_date | 2021-01-01 |
| end_date | 2026-04-15 |
| supersedes | null |
| superseded_by | POS-009 |
| decision | null |

**Responsibilities:** [INFERRED] Engineering operations.

**Notes:** [DIRECT] team-directory.md, Jan 2026. Superseded as part of the May 2026 leadership re-org — Tom was promoted to Head of Platform (see [POS-008](role-assignments.md#pos-008)).

### References
- Person: [PER-005](people.md#per-005)
- Superseded by: [POS-009](role-assignments.md#pos-009)

---

## POS-006: Anika Reddy — Chief AI Officer

| Field | Value |
|-------|-------|
| status | current |
| person | PER-002 |
| role_title | Chief AI Officer |
| team | null |
| start_date | 2026-04-01 |
| end_date | null |
| supersedes | null |
| superseded_by | null |
| decision | DEC-002 |

**Responsibilities:** [UNVERIFIED] Not described beyond the title in team-directory-update.md.

**Notes:** [DIRECT] Newly created role_title — no prior holder, so this is a new entry rather than a supersession.

### References
- Person: [PER-002](people.md#per-002)
- Decision: [DEC-002](decisions.md#dec-002)

---

## POS-007: Yuki Tanaka — Head of Engineering

| Field | Value |
|-------|-------|
| status | current |
| person | PER-004 |
| role_title | Head of Engineering |
| team | null |
| start_date | 2026-04-15 |
| end_date | null |
| supersedes | POS-001 |
| superseded_by | null |
| decision | DEC-002 |

**Responsibilities:** [INFERRED] Engineering leadership for BTS-Synthetic.

**Notes:** [DIRECT] team-directory-update.md, May 2026.

### References
- Person: [PER-004](people.md#per-004)
- Supersedes: [POS-001](role-assignments.md#pos-001)
- Decision: [DEC-002](decisions.md#dec-002)

---

## POS-008: Tom Bryce — Head of Platform

| Field | Value |
|-------|-------|
| status | current |
| person | PER-005 |
| role_title | Head of Platform |
| team | TEAM-002 |
| start_date | 2026-04-15 |
| end_date | null |
| supersedes | POS-003 |
| superseded_by | null |
| decision | DEC-002 |

**Responsibilities:** [INFERRED] Owns auth, signing, and tenant-config services (Yuki's prior portfolio).

**Notes:** [DIRECT] team-directory-update.md, May 2026 ("promoted to Head of Platform, replacing Yuki in that role"). `start_date` [INFERRED] aligned with Yuki's Head of Engineering start date — no independently stated date for Tom's promotion.

### References
- Person: [PER-005](people.md#per-005)
- Team: [TEAM-002](teams.md#team-002)
- Supersedes: [POS-003](role-assignments.md#pos-003)
- Decision: [DEC-002](decisions.md#dec-002)

---

## POS-009: Priya Shah — Engineering Ops Lead

| Field | Value |
|-------|-------|
| status | current |
| person | PER-012 |
| role_title | Engineering Ops Lead |
| team | null |
| start_date | 2026-04-15 |
| end_date | null |
| supersedes | POS-005 |
| superseded_by | null |
| decision | DEC-002 |

**Responsibilities:** [INFERRED] Engineering operations (Tom's prior portfolio).

**Notes:** [DIRECT] team-directory-update.md, May 2026 ("now held by Priya Shah, who moved over from leading the Web team"). `start_date` [INFERRED] aligned with the rest of the reshuffle — no independently stated date. Her prior "leading the Web team" role was never formally tracked in role-assignments.md (no role_title/date was ever stated for it in round 1 data), so no corresponding entry is superseded here.

### References
- Person: [PER-012](people.md#per-012)
- Supersedes: [POS-005](role-assignments.md#pos-005)
- Decision: [DEC-002](decisions.md#dec-002)

---
