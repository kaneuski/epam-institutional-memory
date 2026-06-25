---
type: onboarding-stage
tier: traceability
lifecycle: static
id_prefix: STAGE
singleton_key: null
source_doc_types: ["onboarding-handbook"]
last_updated: 2026-06-24
---

# Onboarding Stages

Sequential new-hire journey stages from the onboarding handbook.

---

## STAGE-001: Equipment and Accounts

| Field | Value |
|-------|-------|
| sequence_order | 1 |
| day_range | Day 1 |
| handbook_version | 4.2 |
| policy_ref | null |
| access_tier_ref | null |

**Activities:** Receive a laptop and YubiKey; get credentials for email, Slack, GitHub (`bts-synthetic` org), and read-only staging access. No prod access is granted on day 1.

**Equipment/accounts granted:** Laptop, YubiKey, email, Slack, GitHub, read-only staging environment access.

### References
- (none — no prod policy or access tier applies on day 1)

---

## STAGE-002: Buddy and Team Onboarding

| Field | Value |
|-------|-------|
| sequence_order | 2 |
| day_range | Day 2-5 |
| handbook_version | 4.2 |
| policy_ref | null |
| access_tier_ref | null |

**Activities:** Paired with a buddy for the first two weeks; codebase tour, git workflow (trunk-based, all changes via PR, two approvals to merge), on-call rotation overview, blameless post-mortem culture (written within 48 hours of any P0/P1).

**Equipment/accounts granted:** None beyond Stage 1.

### References
- (none — buddy is assigned by the manager, no specific team/person named in the handbook)

---

## STAGE-003: Getting Prod Access (Read-Only)

| Field | Value |
|-------|-------|
| sequence_order | 3 |
| day_range | Week 2+ |
| handbook_version | 4.2 |
| policy_ref | POL-002 |
| access_tier_ref | AT-001 |

**Activities:** Open a ticket in `#sre-access-requests`; tag manager and the SRE on rota (per the PagerDuty on-call schedule); pair with the SRE on access tooling; SRE files the access in the IAM tool. Access is granted within 4 working hours of pairing.

**Equipment/accounts granted:** Read-only production access.

**Stale-content notice:** `policy_ref` repointed to [POL-002](policies.md#pol-002) (POL-001 is superseded), but this Activities text still describes the old Slack-ticket + SRE-pairing process from handbook v4.2 — POL-002 replaced it with online certification + JIT access via the IAM platform. The pointer is current; the prose is not. Re-ingest an updated onboarding-handbook.md to refresh it.

### References
- Access tier referenced: [AT-001](access-tiers.md#at-001)
- Policy referenced: [POL-001](policies.md#pol-001)

---
