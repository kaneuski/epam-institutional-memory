---
type: service-ownership
tier: core
lifecycle: evolving
id_prefix: OWN
singleton_key: "service"
source_doc_types: ["onboarding-handbook", "team-directory-update"]
last_updated: 2026-06-24
---

# Service Ownership

Which team/lead owns which service, with supersession history. At most one status:current entry per service.

---

## OWN-001: payment-service Ownership

| Field | Value |
|-------|-------|
| status | former |
| service | SYS-001 |
| owning_team | TEAM-003 |
| tech_lead | PER-005 |
| start_date | 2026-01-01 |
| end_date | 2026-04-15 |
| supersedes | null |
| decision | null |

**Notes:** [DIRECT] from onboarding-handbook.md service-ownership table. `start_date` is [INFERRED] from the handbook's effective date, not an explicitly stated ownership start. Superseded as part of the May 2026 re-org when Tom Bryce was promoted to Head of Platform.

### References
- Service: [SYS-001](services.md#sys-001)
- Team: [TEAM-003](teams.md#team-003)
- Tech lead: [PER-005](people.md#per-005)
- Superseded by: [OWN-006](service-ownership.md#own-006)

---

## OWN-002: auth-service Ownership

| Field | Value |
|-------|-------|
| status | current |
| service | SYS-002 |
| owning_team | TEAM-002 |
| tech_lead | PER-004 |
| start_date | 2026-01-01 |
| end_date | null |
| supersedes | null |
| decision | null |

**Notes:** [DIRECT] Corroborated by both onboarding-handbook.md's table and team-directory.md ("Yuki Tanaka ... Owns auth, signing, tenant-config services").

### References
- Service: [SYS-002](services.md#sys-002)
- Team: [TEAM-002](teams.md#team-002)
- Tech lead: [PER-004](people.md#per-004)

---

## OWN-003: signing-service Ownership

| Field | Value |
|-------|-------|
| status | current |
| service | SYS-003 |
| owning_team | TEAM-002 |
| tech_lead | PER-004 |
| start_date | 2026-01-01 |
| end_date | null |
| supersedes | null |
| decision | null |

**Notes:** [DIRECT] Corroborated by both onboarding-handbook.md and team-directory.md.

### References
- Service: [SYS-003](services.md#sys-003)
- Team: [TEAM-002](teams.md#team-002)
- Tech lead: [PER-004](people.md#per-004)

---

## OWN-004: tenant-config-service Ownership

| Field | Value |
|-------|-------|
| status | current |
| service | SYS-004 |
| owning_team | TEAM-002 |
| tech_lead | PER-004 |
| start_date | 2026-01-01 |
| end_date | null |
| supersedes | null |
| decision | null |

**Notes:** [DIRECT] Corroborated by both onboarding-handbook.md and team-directory.md.

### References
- Service: [SYS-004](services.md#sys-004)
- Team: [TEAM-002](teams.md#team-002)
- Tech lead: [PER-004](people.md#per-004)

---

## OWN-005: frontend Ownership

| Field | Value |
|-------|-------|
| status | former |
| service | SYS-005 |
| owning_team | TEAM-004 |
| tech_lead | PER-012 |
| start_date | 2026-01-01 |
| end_date | 2026-04-15 |
| supersedes | null |
| decision | null |

**Notes:** [DIRECT] from onboarding-handbook.md service-ownership table. Tech lead Priya Shah ([PER-012](people.md#per-012)) is a stub — not corroborated elsewhere yet. Superseded as part of the May 2026 re-org when Priya moved to Engineering Ops Lead.

### References
- Service: [SYS-005](services.md#sys-005)
- Team: [TEAM-004](teams.md#team-004)
- Tech lead: [PER-012](people.md#per-012)
- Superseded by: [OWN-007](service-ownership.md#own-007)

---

## OWN-006: payment-service Ownership

| Field | Value |
|-------|-------|
| status | current |
| service | SYS-001 |
| owning_team | TEAM-003 |
| tech_lead | PER-013 |
| start_date | 2026-04-15 |
| end_date | null |
| supersedes | OWN-001 |
| decision | DEC-002 |

**Notes:** [DIRECT] team-directory-update.md, May 2026 ("Was Tom Bryce / Is now Maya Patel (new hire, joined 2026-03)"). `start_date` [INFERRED] aligned with the rest of the reshuffle — not independently stated.

### References
- Service: [SYS-001](services.md#sys-001)
- Team: [TEAM-003](teams.md#team-003)
- Tech lead: [PER-013](people.md#per-013)
- Supersedes: [OWN-001](service-ownership.md#own-001)
- Decision: [DEC-002](decisions.md#dec-002)

---

## OWN-007: frontend Ownership

| Field | Value |
|-------|-------|
| status | current |
| service | SYS-005 |
| owning_team | TEAM-004 |
| tech_lead | PER-014 |
| start_date | 2026-04-15 |
| end_date | null |
| supersedes | OWN-005 |
| decision | DEC-002 |

**Notes:** [DIRECT] team-directory-update.md, May 2026 ("Was Priya Shah / Is now Daniel Okonkwo"). `start_date` [INFERRED] aligned with the rest of the reshuffle — not independently stated.

### References
- Service: [SYS-005](services.md#sys-005)
- Team: [TEAM-004](teams.md#team-004)
- Tech lead: [PER-014](people.md#per-014)
- Supersedes: [OWN-005](service-ownership.md#own-005)
- Decision: [DEC-002](decisions.md#dec-002)

---
