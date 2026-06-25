---
type: team
tier: domain
lifecycle: static
id_prefix: TEAM
singleton_key: null
source_doc_types: ["team-directory"]
last_updated: 2026-06-24
---

# Teams

Team identity and mission.

---

## TEAM-001: SRE Team

| Field | Value |
|-------|-------|
| parent_team | null |

**Mission:** Owns the on-call rotation, P0/P1 incident response, and prod-access pairing sessions for new hires.

### References
- Lead: [POS-002](role-assignments.md#pos-002)
- Members: [PER-003](people.md#per-003), [PER-006](people.md#per-006), [PER-007](people.md#per-007), [PER-008](people.md#per-008), [PER-009](people.md#per-009), [PER-015](people.md#per-015)

---

## TEAM-002: Platform Team

| Field | Value |
|-------|-------|
| parent_team | null |

**Mission:** Owns auth, signing, and tenant-config services.

### References
- Lead: [POS-008](role-assignments.md#pos-008) *(Tom Bryce, since 2026-04-15 — supersedes Yuki Tanaka per team-directory-update.md)*
- Members: [PER-005](people.md#per-005), [PER-010](people.md#per-010), [PER-011](people.md#per-011) *(Yuki Tanaka, [PER-004](people.md#per-004), moved to Head of Engineering and is no longer listed as a Platform Team member)*
- Owns services: [OWN-002](service-ownership.md#own-002), [OWN-003](service-ownership.md#own-003), [OWN-004](service-ownership.md#own-004)

---

## TEAM-003: Payments

| Field | Value |
|-------|-------|
| parent_team | null |

**Mission:** [UNVERIFIED] Not described in any source doc — stub created from the owning-team column of onboarding-handbook.md's service-ownership table. No lead or members named yet.

### References
- Owns services: [OWN-006](service-ownership.md#own-006)

---

## TEAM-004: Web

| Field | Value |
|-------|-------|
| parent_team | null |

**Mission:** [UNVERIFIED] Not described in any source doc — stub created from the owning-team column of onboarding-handbook.md's service-ownership table. No lead or members named at any point — team-directory-update.md mentions Priya Shah ([PER-012](people.md#per-012)) "moved over from leading the Web team" (as of the May 2026 re-org), but no role-assignments.md entry was ever created for that leadership role, so it isn't recorded as a formal Lead reference here.

### References
- Owns services: [OWN-007](service-ownership.md#own-007)

---
